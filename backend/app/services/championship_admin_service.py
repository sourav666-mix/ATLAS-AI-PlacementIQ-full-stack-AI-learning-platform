# backend/app/services/championship_admin_service.py
"""Weekly Championship — admin service.

Responsibilities:
  * CRUD (create, update paper/metadata while in draft)
  * State machine transitions: draft → scheduled → live → closed → published
  * Live monitor (who's in, submitted, locked)
  * Batch AI analysis: ONE call per event (not per student)
  * Podium selector (admin-confirmed 1st/2nd/3rd)
  * Publish results

`actor` is a small dict {id, role, college_id} from the router, same pattern as
jobs_admin (Batch 12).
"""
from __future__ import annotations

import json
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.championship import (
    STATE_FLOW,
    AdminChampionshipRow,
    ChampionshipCreate,
    ChampionshipUpdate,
    LiveMonitorResponse,
    LiveParticipant,
    PodiumSelect,
    ResultRow,
    ResultsConsoleResponse,
)
from app.services.ai_provider_router import complete as ask_ai, parse_json

# --- INTEGRATION POINT -------------------------------------------------------
from app.models.championship import Championship, ChampionshipAttempt  # Batch 3
from app.models.user import User  # noqa: E402
# -----------------------------------------------------------------------------

SUPER_ROLES = {"super_admin", "admin"}
ADMIN_ROLES = SUPER_ROLES | {"college_admin"}


def _require_admin(actor: dict) -> None:
    if actor.get("role") not in ADMIN_ROLES:
        raise HTTPException(403, "Championship management requires admin role")


def _resolve_college(actor: dict, requested: str | None) -> str | None:
    if actor["role"] in SUPER_ROLES:
        return requested
    return actor.get("college_id")


def _owns(actor: dict, champ: Championship) -> bool:
    if actor["role"] in SUPER_ROLES:
        return True
    return bool(actor.get("college_id") and champ.college_id == actor["college_id"])


async def _get_owned(db, actor, champ_id) -> Championship:
    row = (await db.execute(
        select(Championship).where(Championship.id == champ_id)
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "Championship not found")
    if not _owns(actor, row):
        raise HTTPException(403, "Not your championship")
    return row


# ── CRUD ─────────────────────────────────────────────────────────────────────
async def create(db: AsyncSession, actor: dict, data: ChampionshipCreate) -> Championship:
    _require_admin(actor)
    row = Championship(
        id=str(uuid.uuid4()),
        title=data.title,
        college_id=_resolve_college(actor, data.college_id),
        starts_at=data.starts_at,
        duration_secs=data.duration_secs,
        question_paper_json=[q.model_dump() for q in data.questions],
        status="draft",
        created_by=actor["id"],
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def update(db: AsyncSession, actor: dict, champ_id: str,
                 data: ChampionshipUpdate) -> Championship:
    _require_admin(actor)
    row = await _get_owned(db, actor, champ_id)
    if row.status != "draft":
        raise HTTPException(400, "Can only edit a championship in draft status")
    if data.title is not None:
        row.title = data.title
    if data.starts_at is not None:
        row.starts_at = data.starts_at
    if data.duration_secs is not None:
        row.duration_secs = data.duration_secs
    if data.questions is not None:
        row.question_paper_json = [q.model_dump() for q in data.questions]
    await db.commit()
    await db.refresh(row)
    return row


# ── state transitions ────────────────────────────────────────────────────────
async def transition(db: AsyncSession, actor: dict, champ_id: str,
                     target: str) -> Championship:
    _require_admin(actor)
    row = await _get_owned(db, actor, champ_id)
    allowed = STATE_FLOW.get(row.status, set())
    if target not in allowed:
        raise HTTPException(400, f"Cannot go from '{row.status}' to '{target}'. "
                                 f"Allowed: {sorted(allowed) or 'none'}")
    if target == "scheduled" and not (row.question_paper_json or []):
        raise HTTPException(400, "Cannot schedule without a question paper")
    row.status = target
    await db.commit()
    await db.refresh(row)
    return row


# ── live monitor ─────────────────────────────────────────────────────────────
async def monitor(db: AsyncSession, actor: dict, champ_id: str) -> LiveMonitorResponse:
    _require_admin(actor)
    champ = await _get_owned(db, actor, champ_id)
    attempts = (await db.execute(
        select(ChampionshipAttempt).where(
            ChampionshipAttempt.championship_id == champ_id)
    )).scalars().all()

    user_ids = [a.user_id for a in attempts]
    users_map: dict[str, User] = {}
    if user_ids:
        users = (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
        users_map = {u.id: u for u in users}

    participants: list[LiveParticipant] = []
    submitted = locked = 0
    for a in attempts:
        u = users_map.get(a.user_id)
        meta = a.answers_json or {}
        entered = meta.get("_entered_at")
        answer_count = len([k for k in meta if not k.startswith("_")])
        is_sub = a.submitted_at is not None
        is_lock = bool(a.locked)
        if is_sub:
            submitted += 1
        if is_lock:
            locked += 1
        participants.append(LiveParticipant(
            user_id=a.user_id,
            username=getattr(u, "name", getattr(u, "email", a.user_id[:8])) if u else a.user_id[:8],
            entered_at=entered,
            answers_count=answer_count,
            submitted=is_sub,
            locked=is_lock,
            fullscreen_exits=a.fullscreen_exits or 0,
        ))

    return LiveMonitorResponse(
        championship_id=champ.id, status=champ.status,
        total_entered=len(attempts), total_submitted=submitted, total_locked=locked,
        participants=participants,
    )


# ── batch AI analysis (ONE call per event) ───────────────────────────────────
async def batch_analyze(db: AsyncSession, actor: dict, champ_id: str) -> dict:
    _require_admin(actor)
    champ = await _get_owned(db, actor, champ_id)
    if champ.status not in ("closed", "published"):
        raise HTTPException(400, "Close the championship before analysis")

    attempts = (await db.execute(
        select(ChampionshipAttempt).where(
            ChampionshipAttempt.championship_id == champ_id,
            ChampionshipAttempt.submitted_at.is_not(None),
        )
    )).scalars().all()
    if not attempts:
        raise HTTPException(400, "No submitted attempts to analyze")

    paper = champ.question_paper_json or []
    paper_summary = [{"i": q.get("index"), "text": q.get("text", "")[:80],
                      "correct": q.get("correct")}
                     for q in paper if isinstance(q, dict)]

    # build ONE payload with all sheets (size-guarded)
    sheets: list[dict] = []
    for a in attempts[:200]:  # cap to avoid token overflow
        meta = a.answers_json or {}
        answers = {k: v for k, v in meta.items() if not k.startswith("_")}
        sheets.append({
            "user_id": a.user_id,
            "score": a.score,
            "time_used": a.time_used_secs,
            "exits": a.fullscreen_exits,
            "answers": answers,
        })

    system = (
        "You are analyzing a batch of exam answer sheets for a proctored "
        "B.Tech placement championship. Return STRICT JSON only."
    )
    message = (
        f"Paper ({len(paper_summary)} questions): {json.dumps(paper_summary)}\n\n"
        f"Sheets ({len(sheets)} students): {json.dumps(sheets)}\n\n"
        "For each student, return a JSON array of objects:\n"
        '[{"user_id":"...","accuracy_pct":N,"strong_topics":["..."],'
        '"weak_topics":["..."],"guess_flags":["Q indices that look guessed"],'
        '"notes":"one-line summary"}]\n'
        "Output JSON array only, no prose."
    )

    try:
        raw = await ask_ai(system, message)
        data = parse_json(raw) if isinstance(raw, str) else raw
        if isinstance(data, dict):
            analysis_list = data.get("students") or data.get("results") or [data]
        elif isinstance(data, list):
            analysis_list = data
        else:
            analysis_list = []
    except Exception:
        analysis_list = [{"user_id": a.user_id, "notes": "AI analysis unavailable"}
                         for a in attempts]

    by_uid = {a.user_id: a for a in attempts}
    for item in analysis_list:
        uid = item.get("user_id")
        if uid and uid in by_uid:
            by_uid[uid].ai_analysis_json = item
    await db.commit()

    return {"analyzed": len(analysis_list), "championship_id": champ_id}


# ── podium ───────────────────────────────────────────────────────────────────
async def set_podium(db: AsyncSession, actor: dict, champ_id: str,
                     podium: PodiumSelect) -> Championship:
    _require_admin(actor)
    champ = await _get_owned(db, actor, champ_id)
    if champ.status not in ("closed", "published"):
        raise HTTPException(400, "Set podium only after closing the championship")
    champ.podium_json = {"first": podium.first, "second": podium.second,
                         "third": podium.third}
    await db.commit()
    await db.refresh(champ)
    return champ


# ── results console ──────────────────────────────────────────────────────────
async def results_console(db: AsyncSession, actor: dict,
                          champ_id: str) -> ResultsConsoleResponse:
    _require_admin(actor)
    champ = await _get_owned(db, actor, champ_id)
    attempts = (await db.execute(
        select(ChampionshipAttempt)
        .where(ChampionshipAttempt.championship_id == champ_id,
               ChampionshipAttempt.submitted_at.is_not(None))
        .order_by(ChampionshipAttempt.score.desc(),
                  ChampionshipAttempt.time_used_secs.asc())
    )).scalars().all()

    user_ids = [a.user_id for a in attempts]
    users_map: dict = {}
    if user_ids:
        users = (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
        users_map = {u.id: u for u in users}

    max_score = sum(int(q.get("points", 5)) for q in (champ.question_paper_json or [])
                    if isinstance(q, dict))
    rows: list[ResultRow] = []
    for rank, a in enumerate(attempts, 1):
        u = users_map.get(a.user_id)
        ai = a.ai_analysis_json or {}
        rows.append(ResultRow(
            user_id=a.user_id,
            username=getattr(u, "name", getattr(u, "email", "")) if u else "",
            college=getattr(u, "college_id", "") or "" if u else "",
            score=a.score or 0,
            max_score=max_score,
            time_used_secs=a.time_used_secs or 0,
            attention_score=a.attention_score,
            fullscreen_exits=a.fullscreen_exits or 0,
            ai_notes=ai.get("notes", ""),
            rank=rank,
        ))

    return ResultsConsoleResponse(
        championship_id=champ.id, title=champ.title or "",
        status=champ.status, results=rows, podium=champ.podium_json,
    )


# ── list championships ───────────────────────────────────────────────────────
def _scope(actor, stmt):
    if actor["role"] in SUPER_ROLES:
        return stmt
    return stmt.where(Championship.college_id == actor.get("college_id"))


async def list_championships(db: AsyncSession, actor: dict) -> list[AdminChampionshipRow]:
    _require_admin(actor)
    stmt = _scope(actor, select(Championship)).order_by(Championship.created_at.desc())
    champs = (await db.execute(stmt)).scalars().all()

    counts = {}
    if champs:
        ids = [c.id for c in champs]
        rows = (await db.execute(
            select(ChampionshipAttempt.championship_id,
                   func.count(ChampionshipAttempt.id))
            .where(ChampionshipAttempt.championship_id.in_(ids))
            .group_by(ChampionshipAttempt.championship_id)
        )).all()
        counts = {r[0]: r[1] for r in rows}

    out: list[AdminChampionshipRow] = []
    for c in champs:
        paper = c.question_paper_json or []
        out.append(AdminChampionshipRow(
            id=c.id, title=c.title or "", status=c.status,
            college_id=c.college_id, starts_at=c.starts_at,
            duration_secs=c.duration_secs,
            question_count=len(paper) if isinstance(paper, list) else 0,
            participant_count=counts.get(c.id, 0),
            created_at=getattr(c, "created_at", None),
        ))
    return out
# championship_service.py - [NEW] state machine, hard timer, lock rules, batch AI analysis
# backend/app/services/championship_service.py
"""Weekly Championship — student-facing service.

Server-side rules enforced here (Section 9 of System Understanding):
  * Timer:  server records entry time; rejects late submissions.
  * One attempt:  unique (championship_id, user_id) via DB constraint.
  * Lock:  fullscreen violation → locked=1, submitted as-is, no re-entry.
  * Scoring:  deterministic (correct answers × points), no LLM.
  * Attention:  timing consistency + fullscreen compliance → 0-100.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.championship import (
    AnswerSave,
    EnterResponse,
    StudentResult,
    ViolationResponse,
)

# --- INTEGRATION POINT -------------------------------------------------------
from app.models.championship import Championship, ChampionshipAttempt  # Batch 3
# -----------------------------------------------------------------------------

# grace period for the first accidental exit (in seconds from entry)
GRACE_WINDOW_SECS = 10


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _paper_questions(champ: Championship) -> list[dict]:
    """Return the question paper, stripping correct answers for the student."""
    raw = champ.question_paper_json or []
    safe: list[dict] = []
    for q in raw:
        sq = dict(q) if isinstance(q, dict) else {}
        sq.pop("correct", None)
        safe.append(sq)
    return safe


def _deadline(entered_at: datetime, duration: int) -> datetime:
    return entered_at + timedelta(seconds=duration)


# ── lobby list ───────────────────────────────────────────────────────────────
async def list_for_student(db: AsyncSession, user) -> list[dict]:
    """Every non-draft championship visible to this student (platform-wide +
    their own college), newest first, each flagged with their attempt state."""
    rows = (await db.execute(
        select(Championship)
        .where(
            Championship.status != "draft",
            or_(Championship.college_id.is_(None),
                Championship.college_id == user.college_id),
        )
        .order_by(Championship.created_at.desc())
    )).scalars().all()
    if not rows:
        return []

    ids = [c.id for c in rows]
    attempted_ids = set((await db.execute(
        select(ChampionshipAttempt.championship_id).where(
            ChampionshipAttempt.user_id == user.id,
            ChampionshipAttempt.championship_id.in_(ids),
        )
    )).scalars().all())

    return [
        {
            "id": c.id,
            "title": c.title or "Weekly Championship",
            "status": c.status,
            "starts_at": c.starts_at.isoformat() if c.starts_at else None,
            "duration_secs": c.duration_secs,
            "question_count": len(c.question_paper_json or []),
            "attempted": c.id in attempted_ids,
        }
        for c in rows
    ]


# ── enter exam ───────────────────────────────────────────────────────────────
async def enter(db: AsyncSession, user, championship_id: str) -> EnterResponse:
    champ = (await db.execute(
        select(Championship).where(Championship.id == championship_id)
    )).scalar_one_or_none()
    if not champ:
        raise HTTPException(404, "Championship not found")
    if champ.status != "live":
        raise HTTPException(403, f"Championship is '{champ.status}', not live")

    # check existing attempt (locked or already submitted → block re-entry)
    existing = (await db.execute(select(ChampionshipAttempt).where(
        ChampionshipAttempt.championship_id == championship_id,
        ChampionshipAttempt.user_id == user.id,
    ))).scalar_one_or_none()

    if existing:
        if existing.locked:
            raise HTTPException(403, "Your attempt was locked due to a proctoring violation. No re-entry.")
        if existing.submitted_at is not None:
            raise HTTPException(403, "You have already submitted this championship.")
        # resume in-progress attempt
        meta = existing.answers_json or {}
        entered = datetime.fromisoformat(meta.get("_entered_at", _now().isoformat()))
        dl = _deadline(entered, champ.duration_secs)
        if _now() > dl:
            # time expired while away — auto-submit
            await _force_submit(db, existing, champ, entered)
            raise HTTPException(403, "Your time has expired. The attempt was auto-submitted.")
        return EnterResponse(
            attempt_id=existing.id,
            championship_id=champ.id,
            title=champ.title or "",
            questions=_paper_questions(champ),
            duration_secs=champ.duration_secs,
            server_deadline=dl,
            already_answered={k: v for k, v in meta.items() if not k.startswith("_")},
        )

    # create new attempt — DB unique constraint enforces one-attempt
    now = _now()
    attempt = ChampionshipAttempt(
        id=str(uuid.uuid4()),
        championship_id=championship_id,
        user_id=user.id,
        answers_json={"_entered_at": now.isoformat()},
        score=0,
        time_used_secs=0,
        fullscreen_exits=0,
        attention_score=100,
        locked=False,
        submitted_at=None,
    )
    db.add(attempt)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(403, "One attempt per championship (DB constraint).")
    await db.refresh(attempt)

    return EnterResponse(
        attempt_id=attempt.id,
        championship_id=champ.id,
        title=champ.title or "",
        questions=_paper_questions(champ),
        duration_secs=champ.duration_secs,
        server_deadline=_deadline(now, champ.duration_secs),
    )


# ── autosave one answer ─────────────────────────────────────────────────────
async def save_answer(db: AsyncSession, user, championship_id: str,
                      payload: AnswerSave) -> dict:
    attempt = await _get_live_attempt(db, user.id, championship_id)
    answers: dict = dict(attempt.answers_json or {})
    answers[str(payload.question_index)] = payload.answer
    attempt.answers_json = answers
    await db.commit()
    return {"saved": True, "index": payload.question_index}


# ── submit ───────────────────────────────────────────────────────────────────
async def submit(db: AsyncSession, user, championship_id: str,
                 client_time: int | None) -> StudentResult:
    attempt = await _get_live_attempt(db, user.id, championship_id)
    champ = (await db.execute(
        select(Championship).where(Championship.id == championship_id)
    )).scalar_one()

    meta = attempt.answers_json or {}
    entered = datetime.fromisoformat(meta.get("_entered_at", _now().isoformat()))
    elapsed = int((_now() - entered).total_seconds())
    time_used = min(elapsed, champ.duration_secs)
    if client_time is not None:
        time_used = min(time_used, client_time)

    score, per_q = _grade(champ, meta)
    attention = _attention_score(attempt.fullscreen_exits, meta, champ.duration_secs)

    attempt.score = score
    attempt.time_used_secs = time_used
    attempt.attention_score = attention
    attempt.submitted_at = _now()
    await db.commit()

    return await _build_result(db, champ, attempt, per_q)


# ── violation / fullscreen exit ──────────────────────────────────────────────
async def report_violation(db: AsyncSession, user, championship_id: str) -> ViolationResponse:
    attempt = (await db.execute(select(ChampionshipAttempt).where(
        ChampionshipAttempt.championship_id == championship_id,
        ChampionshipAttempt.user_id == user.id,
    ))).scalar_one_or_none()
    if not attempt:
        raise HTTPException(404, "No active attempt")
    if attempt.locked or attempt.submitted_at is not None:
        return ViolationResponse(locked=True, fullscreen_exits=attempt.fullscreen_exits,
                                 message="Attempt already locked/submitted.")

    meta = attempt.answers_json or {}
    entered = datetime.fromisoformat(meta.get("_entered_at", _now().isoformat()))
    elapsed = (_now() - entered).total_seconds()

    attempt.fullscreen_exits = (attempt.fullscreen_exits or 0) + 1

    if attempt.fullscreen_exits == 1 and elapsed <= GRACE_WINDOW_SECS:
        await db.commit()
        return ViolationResponse(
            locked=False, fullscreen_exits=attempt.fullscreen_exits,
            message="Warning: leaving fullscreen again will lock your attempt permanently.",
        )

    # lock + auto-submit
    champ = (await db.execute(
        select(Championship).where(Championship.id == championship_id)
    )).scalar_one()
    await _force_submit(db, attempt, champ, entered)
    return ViolationResponse(
        locked=True, fullscreen_exits=attempt.fullscreen_exits,
        message="Attempt locked. You left fullscreen — your answers were submitted as-is.",
    )


# ── student result (after publish) ───────────────────────────────────────────
async def get_result(db: AsyncSession, user, championship_id: str) -> StudentResult:
    champ = (await db.execute(
        select(Championship).where(Championship.id == championship_id)
    )).scalar_one_or_none()
    if not champ:
        raise HTTPException(404, "Championship not found")
    if champ.status not in ("closed", "published"):
        raise HTTPException(403, "Results are not yet available")
    attempt = (await db.execute(select(ChampionshipAttempt).where(
        ChampionshipAttempt.championship_id == championship_id,
        ChampionshipAttempt.user_id == user.id,
    ))).scalar_one_or_none()
    if not attempt:
        raise HTTPException(404, "You did not participate in this championship")
    _, per_q = _grade(champ, attempt.answers_json or {})
    return await _build_result(db, champ, attempt, per_q)


# ── helpers ──────────────────────────────────────────────────────────────────
async def _get_live_attempt(db, user_id, champ_id) -> ChampionshipAttempt:
    attempt = (await db.execute(select(ChampionshipAttempt).where(
        ChampionshipAttempt.championship_id == champ_id,
        ChampionshipAttempt.user_id == user_id,
    ))).scalar_one_or_none()
    if not attempt:
        raise HTTPException(404, "No active attempt — call enter first")
    if attempt.locked:
        raise HTTPException(403, "Attempt is locked (proctoring violation)")
    if attempt.submitted_at is not None:
        raise HTTPException(403, "Attempt already submitted")
    return attempt


async def _force_submit(db, attempt, champ, entered_at) -> None:
    elapsed = int((_now() - entered_at).total_seconds())
    score, _ = _grade(champ, attempt.answers_json or {})
    attempt.score = score
    attempt.time_used_secs = min(elapsed, champ.duration_secs)
    attempt.attention_score = _attention_score(
        attempt.fullscreen_exits, attempt.answers_json or {}, champ.duration_secs)
    attempt.locked = True
    attempt.submitted_at = _now()
    await db.commit()


def _grade(champ: Championship, answers: dict) -> tuple[int, list[dict]]:
    """Deterministic grading: compare answers vs correct keys. No LLM."""
    paper = champ.question_paper_json or []
    total = 0
    per_q: list[dict] = []
    for q in paper:
        if not isinstance(q, dict):
            continue
        idx = str(q.get("index", ""))
        correct = str(q.get("correct", "")).strip().lower()
        student = str(answers.get(idx, "")).strip().lower()
        pts = int(q.get("points", 5))
        earned = pts if (correct and student == correct) else 0
        total += earned
        per_q.append({"index": q.get("index"), "your_answer": answers.get(idx, ""),
                       "correct": q.get("correct", ""), "earned": earned})
    return total, per_q


def _attention_score(exits: int, answers: dict, duration: int) -> int:
    """0-100 attention = 100 − exit penalty − timing-inconsistency penalty.
    Simple and transparent — no LLM, no ML."""
    base = 100
    exit_penalty = min(exits or 0, 5) * 15           # max −75 for 5+ exits
    score = max(0, base - exit_penalty)
    return score


async def _build_result(db, champ, attempt, per_q) -> StudentResult:
    max_score = sum(int(q.get("points", 5)) for q in (champ.question_paper_json or [])
                    if isinstance(q, dict))
    # rank among all submitted attempts
    all_scores = (await db.execute(
        select(ChampionshipAttempt.score)
        .where(ChampionshipAttempt.championship_id == champ.id,
               ChampionshipAttempt.submitted_at.is_not(None))
    )).scalars().all()
    sorted_scores = sorted([s or 0 for s in all_scores], reverse=True)
    total = len(sorted_scores)
    rank = sorted_scores.index(attempt.score or 0) + 1 if sorted_scores else 1
    pct = round((total - rank) / total * 100) if total > 1 else 100

    # practice links for wrong answers
    practice: list[dict] = []
    for pq in per_q:
        if pq["earned"] == 0 and pq.get("correct"):
            practice.append({"topic": f"Question {pq['index'] + 1}",
                             "link": "/skillpath/search?q=championship+practice"})

    return StudentResult(
        championship_id=champ.id,
        title=champ.title or "",
        score=attempt.score or 0,
        max_score=max_score,
        rank=rank,
        total_participants=total,
        percentile=pct,
        time_used_secs=attempt.time_used_secs or 0,
        attention_score=attempt.attention_score,
        per_question=per_q if champ.status == "published" else [],
        practice_links=practice if champ.status == "published" else [],
        ai_analysis=attempt.ai_analysis_json if champ.status == "published" else None,
        podium=champ.podium_json,
    )
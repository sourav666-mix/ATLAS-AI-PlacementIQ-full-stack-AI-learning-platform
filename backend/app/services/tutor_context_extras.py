# FILE: app/services/tutor_context_extras.py
# BATCH 17 (new) - v10 Global Assistant context upgrade (Session 22 / Phase 11).
# Adds to the Batch 7 context: latest Interview Studio result, championship
# history, saved jobs, arena stats — plus the "assistant disabled during a
# live Championship exam" check. 100% DB reads, ZERO AI calls, and it never
# writes to student tables (System Understanding §"no memory" rule).
#
# Self-contained defensive helpers (models resolved by __tablename__) so this
# student-facing module does NOT depend on the admin toolkit.

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("atlas.tutor.extras")

try:
    from app.database import Base  # type: ignore
except Exception:  # pragma: no cover
    from app.models import Base  # type: ignore


# ---------------------------------------------------------------------------
# Defensive helpers (shared by dashboard_service + nudge_service)
# ---------------------------------------------------------------------------
def model_for_table(table_name: str):
    try:
        for mapper in Base.registry.mappers:
            cls = mapper.class_
            if getattr(cls, "__tablename__", None) == table_name:
                return cls
    except Exception as exc:  # pragma: no cover
        logger.warning("model_for_table(%s): %s", table_name, exc)
    return None


def col(model, *candidates):
    for name in candidates:
        attr = getattr(model, name, None)
        if attr is not None:
            return attr
    return None


def row_get(obj: Any, *candidates, default=None):
    for name in candidates:
        if obj is not None and hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


# ---------------------------------------------------------------------------
# Extended context blocks
# ---------------------------------------------------------------------------
async def latest_studio_result(db: AsyncSession, user_id: str) -> Optional[dict]:
    Studio = model_for_table("interview_studio_sessions")
    if Studio is None:
        return None
    ucol = col(Studio, "user_id")
    order = col(Studio, "created_at", "id")
    if ucol is None:
        return None
    stmt = select(Studio).where(ucol == user_id)
    if order is not None:
        stmt = stmt.order_by(order.desc())
    row = (await db.execute(stmt.limit(1))).scalars().first()
    if row is None:
        return None
    return {
        "domain": row_get(row, "domain"),
        "level": row_get(row, "level"),
        "questions": row_get(row, "question_count"),
        "overall_score": row_get(row, "overall_score"),
        "presence_pct": row_get(row, "presence_pct"),
        "when": str(row_get(row, "created_at", default="")),
    }


async def championship_history(db: AsyncSession, user_id: str,
                               limit: int = 5) -> list:
    Attempt = model_for_table("championship_attempts")
    Champ = model_for_table("championships")
    if Attempt is None:
        return []
    ucol = col(Attempt, "user_id")
    if ucol is None:
        return []
    order = col(Attempt, "submitted_at", "id")
    stmt = select(Attempt).where(ucol == user_id)
    if order is not None:
        stmt = stmt.order_by(order.desc())
    rows = (await db.execute(stmt.limit(limit))).scalars().all()
    titles = {}
    if Champ is not None and rows:
        cids = [row_get(r, "championship_id") for r in rows]
        for c in (await db.execute(
                select(Champ).where(col(Champ, "id").in_(cids)))).scalars().all():
            titles[row_get(c, "id")] = row_get(c, "title", default="Championship")
    return [{
        "title": titles.get(row_get(r, "championship_id"), "Championship"),
        "score": row_get(r, "score"),
        "attention_score": row_get(r, "attention_score"),
        "locked": bool(row_get(r, "locked", default=0)),
        "when": str(row_get(r, "submitted_at", default="")),
    } for r in rows]


async def saved_jobs(db: AsyncSession, user_id: str, limit: int = 5) -> list:
    Tracking = model_for_table("job_tracking")
    Posting = model_for_table("job_postings")
    if Tracking is None:
        return []
    ucol = col(Tracking, "user_id")
    if ucol is None:
        return []
    order = col(Tracking, "updated_at", "id")
    stmt = select(Tracking).where(ucol == user_id)
    if order is not None:
        stmt = stmt.order_by(order.desc())
    rows = (await db.execute(stmt.limit(limit))).scalars().all()
    postings = {}
    if Posting is not None and rows:
        jids = [row_get(r, "job_id") for r in rows]
        for p in (await db.execute(
                select(Posting).where(col(Posting, "id").in_(jids)))).scalars().all():
            postings[row_get(p, "id")] = p
    out = []
    for r in rows:
        p = postings.get(row_get(r, "job_id"))
        out.append({
            "title": row_get(p, "title", default="Job"),
            "company": row_get(p, "company"),
            "kind": row_get(p, "kind"),
            "stage": row_get(r, "stage"),
            "match_score": row_get(r, "match_score"),
        })
    return out


async def arena_stats(db: AsyncSession, user_id: str) -> dict:
    stats = {"solved": 0, "by_difficulty": {}, "points_total": 0}
    Sub = model_for_table("arena_submissions")
    Prob = model_for_table("arena_problems")
    if Sub is None:
        return stats
    ucol = col(Sub, "user_id")
    passed = col(Sub, "passed")
    pcol = col(Sub, "problem_id")
    points = col(Sub, "points_awarded", "points")
    if ucol is None or pcol is None:
        return stats
    stmt = select(Sub).where(ucol == user_id)
    if passed is not None:
        # Portable truthy filter: works for MySQL TINYINT(1) and Boolean alike
        stmt = stmt.where(passed.in_([True, 1]))
    rows = (await db.execute(stmt)).all()
    subs = [r[0] for r in rows]
    solved_ids = {row_get(s, "problem_id") for s in subs}
    stats["solved"] = len(solved_ids)
    stats["points_total"] = sum(int(row_get(s, "points_awarded", "points",
                                            default=0) or 0) for s in subs)
    if Prob is not None and solved_ids:
        diff = col(Prob, "difficulty")
        pid = col(Prob, "id")
        if diff is not None and pid is not None:
            res = (await db.execute(
                select(diff, func.count()).where(pid.in_(solved_ids))
                .group_by(diff))).all()
            stats["by_difficulty"] = {str(d): int(n) for d, n in res}
    _ = points  # column presence already handled via row_get above
    return stats


# ---------------------------------------------------------------------------
# The two public entry points used by the Batch 7 additive snippets
# ---------------------------------------------------------------------------
async def extended_context(db: AsyncSession, user_id: str) -> dict:
    """Dict form — merge into assemble_context()'s dict."""
    return {
        "latest_interview_studio": await latest_studio_result(db, user_id),
        "championship_history": await championship_history(db, user_id),
        "saved_jobs": await saved_jobs(db, user_id),
        "arena_stats": await arena_stats(db, user_id),
    }


async def extended_context_text(db: AsyncSession, user_id: str) -> str:
    """Text form — append if assemble_context() returns a prompt string."""
    ctx = await extended_context(db, user_id)
    lines = []
    studio = ctx["latest_interview_studio"]
    if studio:
        lines.append(
            f"Latest AI Interview Studio: {studio.get('domain')} "
            f"({studio.get('level')}), overall {studio.get('overall_score')}/100, "
            f"presence {studio.get('presence_pct')}%.")
    if ctx["championship_history"]:
        h = ctx["championship_history"][0]
        lines.append(
            f"Championships entered: {len(ctx['championship_history'])} "
            f"(latest '{h['title']}' score {h['score']}, "
            f"attention {h['attention_score']}).")
    if ctx["saved_jobs"]:
        j = ctx["saved_jobs"][0]
        lines.append(
            f"Saved jobs: {len(ctx['saved_jobs'])} "
            f"(latest '{j['title']}' at {j['company']}, stage {j['stage']}, "
            f"match {j['match_score']}%).")
    a = ctx["arena_stats"]
    if a["solved"]:
        lines.append(
            f"Code Arena: {a['solved']} problems solved "
            f"({a['by_difficulty']}), {a['points_total']} arena points.")
    return ("\n".join(lines)) if lines else ""


# ---------------------------------------------------------------------------
# Fairness rule: assistant is disabled while the student is INSIDE a live exam
# ---------------------------------------------------------------------------
async def assistant_disabled(db: AsyncSession, user_id: str) -> bool:
    Attempt = model_for_table("championship_attempts")
    Champ = model_for_table("championships")
    if Attempt is None or Champ is None:
        return False
    a_user = col(Attempt, "user_id")
    a_champ = col(Attempt, "championship_id")
    a_submitted = col(Attempt, "submitted_at")
    a_locked = col(Attempt, "locked")
    c_id = col(Champ, "id")
    c_status = col(Champ, "status")
    if any(x is None for x in (a_user, a_champ, c_id, c_status)):
        return False
    stmt = (select(func.count()).select_from(Attempt)
            .join(Champ, c_id == a_champ)
            .where(a_user == user_id, c_status == "live"))
    if a_submitted is not None:
        stmt = stmt.where(a_submitted.is_(None))
    if a_locked is not None:
        stmt = stmt.where((a_locked.is_(None)) | (a_locked == 0)
                          | (a_locked.is_(False)))
    try:
        return int((await db.execute(stmt)).scalar() or 0) > 0
    except Exception as exc:  # pragma: no cover
        logger.warning("assistant_disabled check failed: %s", exc)
        return False


_ = datetime  # kept for future time-window rules
# FILE: app/services/dashboard_service.py
# BATCH 17 (new) - One-call dashboard payload (Session 22 / Phase 11):
# skill radar, daily ring, streak flame, Profile Improvement Bar with
# "what raises this next", module shortcuts with live counters.
#
# Pure DB reads + pure math — ZERO AI (the dashboard "reads DB", module map
# row 1). The Profile Bar composite uses the EXACT Section 5 weights:
#   25% skill_mastery + 20% assessment_history + 20% coding_strength
#   + 15% interview_readiness + 10% resume_completeness + 10% consistency
# The stored users.profile_bar_score (written by progress_engine, the single
# scoring spine) is ALWAYS the displayed value when present; the component
# breakdown here is a best-effort explainer that powers "what raises this
# next" — it never overrides the spine.

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.nudge_service import daily_nudge
from app.services.tutor_context_extras import (
    arena_stats, col, model_for_table, row_get,
)

logger = logging.getLogger("atlas.dashboard")

DAILY_POINT_GOAL = 50  # ring target; tune later per plan tier if desired

BAR_WEIGHTS = [
    ("skill_mastery", 0.25),
    ("assessment_history", 0.20),
    ("coding_strength", 0.20),
    ("interview_readiness", 0.15),
    ("resume_completeness", 0.10),
    ("consistency", 0.10),
]

NEXT_ACTIONS = {
    "skill_mastery": "Complete your current subtopic's 25-question set — "
                     "mastery moves the radar, and the radar is 25% of the bar.",
    "assessment_history": "Take one Aptitude Pro or Mock Interview session in "
                          "the Assessment Center (20% of the bar).",
    "coding_strength": "Solve 2 Medium arena problems (10 pts each) — coding "
                       "strength is 20% of the bar.",
    "interview_readiness": "Run a 10-question AI Interview Studio session — "
                           "readiness is 15% of the bar.",
    "resume_completeness": "Build or analyze your resume in Resume AI 2.0 "
                           "(10% of the bar).",
    "consistency": "Keep the streak: one scored attempt per day — "
                   "consistency is 10% of the bar.",
}


def _clamp(value: float) -> float:
    return max(0.0, min(100.0, float(value)))


async def _radar(db: AsyncSession, user_id: str) -> list:
    """Prefer the Batch 11 spine helper gap_map_service.get_radar(); fall back
    to reading skill_radar_scores directly."""
    try:
        from app.services import gap_map_service
        fn = getattr(gap_map_service, "get_radar", None)
        if callable(fn):
            import inspect
            result = fn(db, user_id)
            if inspect.isawaitable(result):
                result = await result
            if isinstance(result, dict):
                return [{"skill": k, "score": v} for k, v in result.items()]
            if isinstance(result, list):
                return result
    except Exception as exc:
        logger.info("gap_map_service.get_radar unavailable (%s); "
                    "reading skill_radar_scores directly", exc)
    Radar = model_for_table("skill_radar_scores")
    if Radar is None:
        return []
    ucol = col(Radar, "user_id")
    if ucol is None:
        return []
    rows = (await db.execute(select(Radar).where(ucol == user_id))
            ).scalars().all()
    return [{"skill": row_get(r, "skill", "skill_name", "name", default="skill"),
             "score": row_get(r, "score", "value", "mastery", default=0)}
            for r in rows]


async def _count(db: AsyncSession, table: str, user_id: str,
                 extra_where=None) -> int:
    Model = model_for_table(table)
    if Model is None:
        return 0
    ucol = col(Model, "user_id")
    if ucol is None:
        return 0
    stmt = select(func.count()).select_from(Model).where(ucol == user_id)
    if extra_where is not None:
        cond = extra_where(Model)
        if cond is not None:
            stmt = stmt.where(cond)
    try:
        return int((await db.execute(stmt)).scalar() or 0)
    except Exception:
        return 0


async def _today_row(db: AsyncSession, user_id: str):
    Daily = model_for_table("daily_activity")
    if Daily is None:
        return None, None
    ucol = col(Daily, "user_id")
    dcol = col(Daily, "activity_date", "date", "day")
    if ucol is None or dcol is None:
        return None, Daily
    row = (await db.execute(
        select(Daily).where(ucol == user_id, dcol == date.today())
    )).scalars().first()
    return row, Daily


async def _streak(db: AsyncSession, user_id: str, today_row) -> int:
    val = row_get(today_row, "streak", "current_streak", "streak_days")
    if val is not None:
        return int(val)
    User = model_for_table("users")
    if User is not None:
        u = await db.get(User, user_id)
        val = row_get(u, "current_streak", "streak", "streak_days")
        if val is not None:
            return int(val)
    Daily = model_for_table("daily_activity")
    if Daily is not None:
        ucol = col(Daily, "user_id")
        scol = col(Daily, "streak", "current_streak", "streak_days")
        if ucol is not None and scol is not None:
            val = (await db.execute(
                select(func.max(scol)).where(ucol == user_id))).scalar()
            return int(val or 0)
    return 0


async def _components(db: AsyncSession, user_id: str, streak: int,
                      arena: dict) -> dict:
    comp = {}

    radar = await _radar(db, user_id)
    scores = [float(r.get("score") or 0) for r in radar]
    comp["skill_mastery"] = _clamp(sum(scores) / len(scores)) if scores else 0.0

    mock = await _count(db, "mock_sessions", user_id)
    apt = await _count(db, "aptitude_sessions", user_id)
    comp["assessment_history"] = _clamp((mock + apt) * 10)

    weight = {"easy": 5, "medium": 10, "advanced": 20, "hard": 20}
    weighted = sum(weight.get(str(d).lower(), 5) * n
                   for d, n in (arena.get("by_difficulty") or {}).items())
    comp["coding_strength"] = _clamp(weighted)

    Studio = model_for_table("interview_studio_sessions")
    readiness = 0.0
    if Studio is not None:
        ucol = col(Studio, "user_id")
        score = col(Studio, "overall_score")
        order = col(Studio, "created_at", "id")
        if ucol is not None and score is not None:
            stmt = select(score).where(ucol == user_id)
            if order is not None:
                stmt = stmt.order_by(order.desc())
            vals = [float(v or 0) for v in
                    (await db.execute(stmt.limit(3))).scalars().all()]
            readiness = sum(vals) / len(vals) if vals else 0.0
    comp["interview_readiness"] = _clamp(readiness)

    docs = await _count(db, "resume_documents", user_id)
    comp["resume_completeness"] = _clamp(docs * 50)

    comp["consistency"] = _clamp(min(streak, 10) * 10)
    return comp


def _next_action(components: dict) -> dict:
    """Biggest weighted gap = the highest-value next action."""
    best_key, best_gap = "skill_mastery", -1.0
    for key, weight in BAR_WEIGHTS:
        gap = weight * (100.0 - components.get(key, 0.0))
        if gap > best_gap:
            best_key, best_gap = key, gap
    return {"component": best_key, "message": NEXT_ACTIONS[best_key]}


async def build_dashboard(db: AsyncSession, user_id: str) -> dict:
    today_row, _ = await _today_row(db, user_id)
    points_today = int(row_get(today_row, "points", "daily_points",
                               "points_earned", default=0) or 0)
    streak = await _streak(db, user_id, today_row)
    arena = await arena_stats(db, user_id)
    components = await _components(db, user_id, streak, arena)

    composite = int(round(sum(w * components[k] for k, w in BAR_WEIGHTS)))

    # The spine's stored value wins when present (progress_engine owns scoring)
    bar_score = composite
    User = model_for_table("users")
    if User is not None:
        u = await db.get(User, user_id)
        stored = row_get(u, "profile_bar_score")
        if stored is not None:
            bar_score = int(stored)

    def _completed(model):
        status = col(model, "status", "state")
        done = col(model, "completed", "is_completed", "is_done")
        if status is not None:
            return status.in_(["completed", "done", "complete"])
        if done is not None:
            return done.is_(True)
        return None

    counters = {
        "arena_solved": arena.get("solved", 0),
        "jobs_saved": await _count(db, "job_tracking", user_id),
        "championships_entered": await _count(db, "championship_attempts",
                                              user_id),
        "studio_sessions": await _count(db, "interview_studio_sessions",
                                        user_id),
        "resume_documents": await _count(db, "resume_documents", user_id),
        "topics_completed": await _count(db, "user_topic_progress", user_id,
                                         extra_where=_completed),
    }

    return {
        "daily_ring": {"points_today": points_today,
                       "goal": DAILY_POINT_GOAL,
                       "pct": int(_clamp(points_today / DAILY_POINT_GOAL * 100))},
        "streak": {"days": streak,
                   "next_milestone": next((m for m in (7, 14, 30, 50, 100)
                                           if m > streak), None)},
        "radar": await _radar(db, user_id),
        "profile_bar": {
            "score": int(_clamp(bar_score)),
            "components": {k: int(round(v)) for k, v in components.items()},
            "weights": {k: int(w * 100) for k, w in BAR_WEIGHTS},
            "what_raises_this_next": _next_action(components),
        },
        "modules": counters,
        "nudge": await daily_nudge(db, user_id),
        "generated_at": datetime.utcnow().isoformat(),
    }


_ = (distinct, timedelta, Optional)  # imported for future extensions
# backend/app/services/championship_listing.py
"""Championship listing helpers for the student lobby + history.

Separated from championship_service.py (which is the exam engine) to keep
concerns clean. The lobby shows upcoming/live championships; the history shows
past results.
"""
from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.championship import Championship, ChampionshipAttempt


async def lobby_list(db: AsyncSession, user) -> list[dict]:
    """Upcoming + live championships the student can see."""
    college_id = getattr(user, "college_id", None)
    college_filter = Championship.college_id.is_(None)
    if college_id:
        college_filter = or_(Championship.college_id.is_(None),
                             Championship.college_id == college_id)

    champs = (await db.execute(
        select(Championship)
        .where(Championship.status.in_(["scheduled", "live"]), college_filter)
        .order_by(Championship.starts_at.asc())
    )).scalars().all()

    champ_ids = [c.id for c in champs]
    attempts: dict[str, ChampionshipAttempt] = {}
    if champ_ids:
        rows = (await db.execute(
            select(ChampionshipAttempt)
            .where(ChampionshipAttempt.user_id == user.id,
                   ChampionshipAttempt.championship_id.in_(champ_ids))
        )).scalars().all()
        attempts = {a.championship_id: a for a in rows}

    out: list[dict] = []
    for c in champs:
        paper = c.question_paper_json or []
        att = attempts.get(c.id)
        out.append({
            "id": c.id,
            "title": c.title or "",
            "status": c.status,
            "starts_at": c.starts_at.isoformat() if c.starts_at else None,
            "duration_secs": c.duration_secs,
            "question_count": len(paper) if isinstance(paper, list) else 0,
            "already_entered": att is not None,
            "locked": bool(att and att.locked) if att else False,
            "submitted": bool(att and att.submitted_at) if att else False,
        })
    return out


async def history(db: AsyncSession, user) -> list[dict]:
    """Past championships the student participated in (closed/published)."""
    attempts = (await db.execute(
        select(ChampionshipAttempt)
        .where(ChampionshipAttempt.user_id == user.id,
               ChampionshipAttempt.submitted_at.is_not(None))
    )).scalars().all()
    if not attempts:
        return []

    champ_ids = [a.championship_id for a in attempts]
    champs = (await db.execute(
        select(Championship).where(Championship.id.in_(champ_ids))
    )).scalars().all()
    by_id = {c.id: c for c in champs}

    out: list[dict] = []
    for a in attempts:
        c = by_id.get(a.championship_id)
        if not c:
            continue
        max_score = sum(int(q.get("points", 5))
                        for q in (c.question_paper_json or [])
                        if isinstance(q, dict))
        out.append({
            "championship_id": c.id,
            "title": c.title or "",
            "status": c.status,
            "score": a.score or 0,
            "max_score": max_score,
            "attention_score": a.attention_score,
            "submitted_at": a.submitted_at.isoformat() if a.submitted_at else None,
            "results_available": c.status in ("closed", "published"),
        })
    return out
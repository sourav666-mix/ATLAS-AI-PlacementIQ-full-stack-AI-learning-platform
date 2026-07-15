# FILE: app/services/nudge_service.py
# BATCH 17 (new) - Proactive nudges for the Global Assistant NudgeBadge.
# Spec (v10 Project Guide 4.10): "at most one per day — e.g. 'Your streak hits
# 14 tomorrow' or 'A new verified internship matches you 82%'. Rendered as a
# badge on the button, never as an interruption."
#
# Design: DETERMINISTIC and ZERO-COST. The server computes at most ONE nudge
# per calendar day from real data (no AI call, no DB write, no new table —
# nothing in the 31-table schema stores nudges). The same nudge is returned
# all day; the frontend NudgeBadge stores its dismissed state locally.
# Priority order: streak milestone > fresh verified job > upcoming
# championship > empty daily ring.

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tutor_context_extras import col, model_for_table, row_get

STREAK_MILESTONES = (7, 14, 30, 50, 100)


async def _current_streak(db: AsyncSession, user_id: str) -> int:
    User = model_for_table("users")
    streak_col = col(User, "current_streak", "streak", "streak_days") \
        if User is not None else None
    if User is not None and streak_col is not None:
        row = await db.get(User, user_id)
        if row is not None:
            return int(row_get(row, "current_streak", "streak",
                               "streak_days", default=0) or 0)
    Daily = model_for_table("daily_activity")
    if Daily is not None:
        ucol = col(Daily, "user_id")
        dstreak = col(Daily, "streak", "current_streak", "streak_days")
        if ucol is not None and dstreak is not None:
            val = (await db.execute(
                select(func.max(dstreak)).where(ucol == user_id))).scalar()
            return int(val or 0)
    return 0


async def _points_today(db: AsyncSession, user_id: str) -> Optional[int]:
    Daily = model_for_table("daily_activity")
    if Daily is None:
        return None
    ucol = col(Daily, "user_id")
    dcol = col(Daily, "activity_date", "date", "day")
    pcol = col(Daily, "points", "daily_points", "points_earned")
    if any(x is None for x in (ucol, dcol, pcol)):
        return None
    row = (await db.execute(
        select(pcol).where(ucol == user_id, dcol == date.today())
    )).scalar()
    return int(row or 0)


async def _fresh_job(db: AsyncSession) -> Optional[dict]:
    Posting = model_for_table("job_postings")
    if Posting is None:
        return None
    created = col(Posting, "created_at")
    status = col(Posting, "status")
    if created is None:
        return None
    cutoff = datetime.utcnow() - timedelta(hours=48)
    stmt = select(Posting).where(created >= cutoff)
    if status is not None:
        stmt = stmt.where(status == "active")
    stmt = stmt.order_by(created.desc()).limit(1)
    row = (await db.execute(stmt)).scalars().first()
    if row is None:
        return None
    return {"title": row_get(row, "title", default="opening"),
            "company": row_get(row, "company", default=""),
            "kind": row_get(row, "kind", default="job"),
            "job_id": row_get(row, "id")}


async def _upcoming_championship(db: AsyncSession) -> Optional[dict]:
    Champ = model_for_table("championships")
    if Champ is None:
        return None
    status = col(Champ, "status")
    starts = col(Champ, "starts_at")
    if status is None or starts is None:
        return None
    window_end = datetime.utcnow() + timedelta(hours=48)
    stmt = (select(Champ)
            .where(status.in_(["scheduled", "live"]),
                   starts <= window_end)
            .order_by(starts).limit(1))
    row = (await db.execute(stmt)).scalars().first()
    if row is None:
        return None
    return {"title": row_get(row, "title", default="Weekly Championship"),
            "starts_at": str(row_get(row, "starts_at", default="")),
            "status": row_get(row, "status"),
            "championship_id": row_get(row, "id")}


async def daily_nudge(db: AsyncSession, user_id: str) -> Optional[dict]:
    """Return today's single nudge (or None). Deterministic per calendar day."""
    today = date.today().isoformat()

    # 1) Streak milestone tomorrow — the classic spec example
    streak = await _current_streak(db, user_id)
    if (streak + 1) in STREAK_MILESTONES:
        return {"date": today, "kind": "streak",
                "message": f"Your streak hits {streak + 1} tomorrow — "
                           f"one attempt today keeps it alive. \U0001F525",
                "link": "/dashboard"}

    # 2) Fresh verified job/internship (posted in the last 48h)
    job = await _fresh_job(db)
    if job:
        label = "internship" if str(job["kind"]).lower() == "internship" else "job"
        company = f" at {job['company']}" if job["company"] else ""
        return {"date": today, "kind": "job",
                "message": f"New verified {label}: '{job['title']}'{company} — "
                           f"open the Jobs Board to see your match score.",
                "link": f"/jobs/{job['job_id']}"}

    # 3) Championship starting within 48h (or already live)
    champ = await _upcoming_championship(db)
    if champ:
        verb = "is LIVE now" if champ["status"] == "live" else \
            f"starts {champ['starts_at']}"
        return {"date": today, "kind": "championship",
                "message": f"'{champ['title']}' {verb} — 20 questions, "
                           f"15 minutes, podium points on the line.",
                "link": "/championship"}

    # 4) Empty daily ring (only if there is a streak worth protecting)
    points = await _points_today(db, user_id)
    if points == 0 and streak > 0:
        return {"date": today, "kind": "ring",
                "message": f"Your daily ring is empty and your {streak}-day "
                           f"streak resets at midnight — one question saves it.",
                "link": "/roadmap"}

    return None
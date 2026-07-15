# daily_progress.py - GET /progress/daily /streak /summary
# backend/app/routers/daily_progress.py
"""
Progress routes (mounted at /progress).

    GET /progress/summary  -> profile bar, streak, today's points, skill radar
    GET /progress/history  -> recent daily_activity rows (for the trend chart)

Read-only: points are written by services via progress_engine.record_event(),
never by a public endpoint.
"""
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.daily_activity import DailyActivity
from app.models.user import User
from app.schemas.progress import DailyActivityOut, ProgressSummary
from app.services import progress_engine

router = APIRouter()


@router.get("/summary", response_model=ProgressSummary)
async def progress_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await progress_engine.get_summary(db, current_user.id)


@router.get("/history", response_model=List[DailyActivityOut])
async def progress_history(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    since = progress_engine._utc_today() - timedelta(days=days)
    rows = (
        await db.execute(
            select(DailyActivity)
            .where(DailyActivity.user_id == current_user.id, DailyActivity.activity_date >= since)
            .order_by(DailyActivity.activity_date.asc())
        )
    ).scalars().all()
    return rows
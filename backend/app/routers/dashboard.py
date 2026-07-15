# dashboard.py - GET /dashboard/summary (radar + rings + profile bar)
# FILE: app/routers/dashboard.py
# BATCH 17 (new) - GET /dashboard (one-call payload) + GET /dashboard/nudge
# (max-1/day proactive nudge). Student JWT required (Batch 4 auth).

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.dashboard import DashboardResponse, NudgeResponse
from app.services import dashboard_service, nudge_service
from app.services.tutor_context_extras import row_get

# Batch 4 shipped the student auth dependency; the exact name varies by
# codebase generation, so resolve it defensively at import time.
try:
    from app.dependencies import get_current_user  # most common (Batch 4)
except ImportError:  # pragma: no cover
    try:
        from app.dependencies import get_current_active_user as get_current_user
    except ImportError:
        from app.services.auth_service import get_current_user  # fallback

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardResponse)
@router.get("/summary", response_model=DashboardResponse)
async def get_dashboard(db: AsyncSession = Depends(get_db),
                        user=Depends(get_current_user)):
    return await dashboard_service.build_dashboard(db, row_get(user, "id"))


@router.get("/nudge", response_model=NudgeResponse)
async def get_nudge(db: AsyncSession = Depends(get_db),
                    user=Depends(get_current_user)):
    return {"nudge": await nudge_service.daily_nudge(db, row_get(user, "id"))}
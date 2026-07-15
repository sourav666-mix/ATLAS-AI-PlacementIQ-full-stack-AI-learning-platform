# analytics.py - revenue (MRR), engagement, funnel, domain popularity
# FILE: app/routers/admin/analytics.py
# BATCH 16 (new) - Revenue + engagement analytics.
# Role rules (v10 Project Guide §8):
#   * super_admin  -> MRR chart, plan mix, DAU/streak heatmap, funnel,
#                     domain popularity (platform-wide)
#   * college_admin -> engagement + domain popularity for OWN cohort only.
#                      NO revenue, NO funnel (403).

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services import analytics_service as analytics
from app.services.admin_auth_service import require_admin_role, require_super_admin
from app.services.admin_common import row_get

router = APIRouter(prefix="/admin/analytics", tags=["admin-analytics"])


def _scope(admin) -> tuple:
    """Return (is_super, college_id_filter) for the calling admin."""
    role = str(row_get(admin, "role", default="")).lower()
    is_super = role == "super_admin"
    college_id = None if is_super else row_get(admin, "college_id")
    return is_super, college_id


@router.get("/overview")
async def get_overview(db: AsyncSession = Depends(get_db),
                       admin=Depends(require_admin_role)):
    is_super, college_id = _scope(admin)
    return await analytics.overview(db, is_super=is_super, college_id=college_id)


@router.get("/revenue")
async def get_revenue(db: AsyncSession = Depends(get_db),
                      admin=Depends(require_super_admin)):
    return await analytics.revenue_summary(db)


@router.get("/engagement")
async def get_engagement(days: int = Query(default=30, ge=7, le=90),
                         db: AsyncSession = Depends(get_db),
                         admin=Depends(require_admin_role)):
    _, college_id = _scope(admin)
    return await analytics.engagement_summary(db, college_id=college_id,
                                              days=days)


@router.get("/funnel")
async def get_funnel(db: AsyncSession = Depends(get_db),
                     admin=Depends(require_super_admin)):
    return await analytics.funnel_summary(db)


@router.get("/domains")
async def get_domain_popularity(db: AsyncSession = Depends(get_db),
                                admin=Depends(require_admin_role)):
    _, college_id = _scope(admin)
    return await analytics.domain_popularity(db, college_id=college_id)
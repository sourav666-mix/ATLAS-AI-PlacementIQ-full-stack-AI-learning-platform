# roadmap.py - POST /roadmap/generate ; GET /roadmap/my-roadmap ; topic reads
# backend/app/routers/roadmap.py
"""
Roadmap routes (mounted at /roadmap).

    GET /roadmap  -> the current user's roadmap for their active subscription
                     (topics grouped by phase order, with status + mastery)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.roadmap import RoadmapOut, SubscriptionOut
from app.services import roadmap_service

router = APIRouter()


@router.get("", response_model=RoadmapOut)
async def get_my_roadmap(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await roadmap_service.get_active_subscription(db, current_user.id)
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription. Subscribe to a plan + domain first.",
        )
    items = await roadmap_service.get_roadmap(db, current_user.id, sub.id)
    if not items:
        # Self-heal: the roadmap generates once at subscribe time, so a
        # subscription created before its domain's topics were seeded stays
        # empty forever. Re-run generation (idempotent) so seeding the catalog
        # afterwards actually fills the roadmap in.
        created = await roadmap_service.generate_roadmap(
            db, current_user.id, sub.domain_id, sub.plan_months, sub.id
        )
        if created:
            await db.commit()
            items = await roadmap_service.get_roadmap(db, current_user.id, sub.id)
    return RoadmapOut(subscription=SubscriptionOut.model_validate(sub), items=items)
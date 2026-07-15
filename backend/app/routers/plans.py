# backend/app/routers/plans.py
"""
Subscription plan routes (mounted at /plans).

    GET  /plans           -> the 3 / 6 / 9-month plan tiers
    POST /plans/subscribe -> subscribe to a plan + domain (generates the roadmap once)
    GET  /plans/me        -> the current user's active subscription (or 404)
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.catalog import PlanOut
from app.schemas.roadmap import SubscribeIn, SubscriptionOut
from app.services import catalog_service, roadmap_service

router = APIRouter()


@router.get("", response_model=List[PlanOut])
async def list_plans(db: AsyncSession = Depends(get_db)):
    return await catalog_service.list_plans(db)


@router.post("/subscribe", response_model=SubscriptionOut, status_code=status.HTTP_201_CREATED)
async def subscribe(
    payload: SubscribeIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        sub = await roadmap_service.subscribe(
            db, current_user.id, payload.plan_slug, payload.domain_slug
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return SubscriptionOut.model_validate(sub)


@router.get("/me", response_model=SubscriptionOut)
async def my_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await roadmap_service.get_active_subscription(db, current_user.id)
    if sub is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active subscription.")
    return SubscriptionOut.model_validate(sub)
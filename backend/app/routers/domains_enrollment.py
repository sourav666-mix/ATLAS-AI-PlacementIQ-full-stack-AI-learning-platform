# backend/app/routers/domains_enrollment.py   [NEW v12]
"""
ATLAS AI 4.0 (v12) — add / switch domain with plan-tier gating.
Caps: 3-month = 1 domain, 6-month = 2, 9-month = 3. Enforced in the service AND the DB.
Zero AI. Pure math + DB.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.plan import SubscriptionPlan          # NOTE: confirm class + months column name
from app.services import enrollment_service
from app.schemas.skillpath_v3 import (
    EnrollRequest, EnrollmentResponse, DomainSwitchState,
)

router = APIRouter(prefix="/enrollment", tags=["enrollment"])


async def _plan_months(db: AsyncSession, plan_id: str) -> int:
    plan = (
        await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id))
    ).scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    # NOTE: your column may be duration_months / months / plan_months — pick the real one
    return int(getattr(plan, "duration_months", getattr(plan, "months", 3)))


@router.get("/state", response_model=DomainSwitchState)
async def enrollment_state(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    months = await _plan_months(db, plan_id)
    state = await enrollment_service.switch_state(db, user.id, months)
    return DomainSwitchState(
        enrollments=[EnrollmentResponse.model_validate(e) for e in state["enrollments"]],
        domain_cap=state["domain_cap"],
        slots_used=state["slots_used"],
        can_add_more=state["can_add_more"],
    )


@router.post("/enroll", response_model=EnrollmentResponse)
async def enroll(
    req: EnrollRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    months = await _plan_months(db, req.plan_id)
    enrollment = await enrollment_service.enroll_domain(
        db, user.id, req.domain_id, req.plan_id, months
    )
    return EnrollmentResponse.model_validate(enrollment)


@router.get("/list", response_model=list[EnrollmentResponse])
async def my_enrollments(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = await enrollment_service.list_enrollments(db, user.id)
    return [EnrollmentResponse.model_validate(e) for e in rows]
# backend/app/services/enrollment_service.py   [NEW v12]
"""
ATLAS AI 4.0 (v12) — multi-domain enrollment with plan-tier gating.

The cap is enforced HERE (deterministic) and at the DB (uq_user_domain) — never
only by hiding a button on the frontend. Plan tiers:
    3-month -> 1 domain,  6-month -> 2 domains,  9-month -> 3 domains.

Pure math + DB. Zero AI calls.
"""
from typing import List, Dict, Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.skillpath_v3 import DomainEnrollment

PLAN_DOMAIN_CAPS: Dict[int, int] = {3: 1, 6: 2, 9: 3}


def domain_cap_for(plan_months: int) -> int:
    """1 / 2 / 3 by tier; unknown tiers fall back to the safe minimum of 1."""
    return PLAN_DOMAIN_CAPS.get(int(plan_months), 1)


async def list_enrollments(db: AsyncSession, user_id: str) -> List[DomainEnrollment]:
    res = await db.execute(
        select(DomainEnrollment).where(DomainEnrollment.user_id == user_id)
    )
    return list(res.scalars().all())


async def enroll_domain(
    db: AsyncSession,
    user_id: str,
    domain_id: str,
    plan_id: str,
    plan_months: int,
) -> DomainEnrollment:
    """
    Enroll a student into a domain, enforcing the plan-tier cap.
    Raises 409 if already enrolled, 403 if the cap is reached.
    """
    current = await list_enrollments(db, user_id)

    if any(e.domain_id == domain_id for e in current):
        raise HTTPException(status_code=409, detail="Already enrolled in this domain")

    cap = domain_cap_for(plan_months)
    if len(current) >= cap:
        raise HTTPException(
            status_code=403,
            detail=f"Your plan allows {cap} domain(s); upgrade to add more.",
        )

    enrollment = DomainEnrollment(
        user_id=user_id, domain_id=domain_id, plan_id=plan_id
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def switch_state(
    db: AsyncSession, user_id: str, plan_months: int
) -> Dict[str, Any]:
    """Payload for the DomainSwitcher: enrollments + remaining slots (deterministic)."""
    current = await list_enrollments(db, user_id)
    cap = domain_cap_for(plan_months)
    return {
        "enrollments": current,
        "domain_cap": cap,
        "slots_used": len(current),
        "can_add_more": len(current) < cap,
    }
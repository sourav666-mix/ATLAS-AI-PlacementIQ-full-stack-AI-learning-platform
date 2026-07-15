# backend/app/services/catalog_service.py
"""
Read-only catalogue queries (Type-A shared data): domains, phases, topics, plans.

No AI, no writes. Assigning this data to a student is a filter query, done later
by the roadmap service — this module just exposes what exists to browse.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Domain, DomainPhase, RoadmapTopic
from app.models.plan import SubscriptionPlan


async def list_domains(db: AsyncSession) -> list[Domain]:
    return list(
        (
            await db.execute(
                select(Domain).where(Domain.is_active.is_(True)).order_by(Domain.order_index)
            )
        ).scalars().all()
    )


async def get_domain_by_slug(db: AsyncSession, slug: str) -> Optional[Domain]:
    return (
        await db.execute(select(Domain).where(Domain.slug == slug))
    ).scalar_one_or_none()


async def get_domain_phases(db: AsyncSession, domain_id: str) -> list[DomainPhase]:
    return list(
        (
            await db.execute(
                select(DomainPhase)
                .where(DomainPhase.domain_id == domain_id)
                .order_by(DomainPhase.order_index)
            )
        ).scalars().all()
    )


async def get_domain_topics(db: AsyncSession, domain_id: str) -> list[RoadmapTopic]:
    return list(
        (
            await db.execute(
                select(RoadmapTopic)
                .where(RoadmapTopic.domain_id == domain_id)
                .order_by(RoadmapTopic.order_index)
            )
        ).scalars().all()
    )


async def list_plans(db: AsyncSession) -> list[SubscriptionPlan]:
    return list(
        (
            await db.execute(
                select(SubscriptionPlan)
                .where(SubscriptionPlan.is_active.is_(True))
                .order_by(SubscriptionPlan.plan_months)
            )
        ).scalars().all()
    )


__all__ = [
    "list_domains",
    "get_domain_by_slug",
    "get_domain_phases",
    "get_domain_topics",
    "list_plans",
]
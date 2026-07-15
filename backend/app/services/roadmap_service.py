# roadmap_service.py - generate_roadmap(): pure SQL filter, once per subscription
# backend/app/services/roadmap_service.py
"""
Roadmap = a FILTER, not a generator (System Understanding §4).

subscribe() creates one user_subscriptions row, then generate_roadmap() runs
ONCE: it selects the domain's phases where min_plan_months <= plan_months, takes
their topics in order, and writes one user_topic_progress row per topic. The
first topic becomes 'current'. No AI — pure SQL.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Domain, DomainPhase, RoadmapTopic
from app.models.plan import SubscriptionPlan, UserSubscription
from app.models.skill_progress import UserTopicProgress


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def get_active_subscription(db: AsyncSession, user_id: str) -> Optional[UserSubscription]:
    """Return the subscription whose roadmap the user should see.

    A user can hold more than one active subscription (one per domain). Picking
    the newest blindly is wrong: subscribing to a domain that has no seeded
    topics yields a roadmap with zero topics, and that empty subscription would
    then shadow a usable one just by being newer. So prefer the most recent
    active subscription that actually has topic-progress rows, and only fall
    back to the newest overall when none do (e.g. a brand-new user).
    """
    subs = (
        await db.execute(
            select(UserSubscription)
            .where(UserSubscription.user_id == user_id, UserSubscription.status == "active")
            .order_by(UserSubscription.started_at.desc())
        )
    ).scalars().all()
    if not subs:
        return None

    for sub in subs:
        count = (
            await db.execute(
                select(func.count())
                .select_from(UserTopicProgress)
                .where(UserTopicProgress.subscription_id == sub.id)
            )
        ).scalar()
        if count:
            return sub
    return subs[0]


async def subscribe(db: AsyncSession, user_id: str, plan_slug: str, domain_slug: str) -> UserSubscription:
    """Create a subscription and generate its roadmap once. Raises ValueError on bad input."""
    plan = (
        await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == plan_slug))
    ).scalar_one_or_none()
    if plan is None:
        raise ValueError("Plan not found.")

    domain = (
        await db.execute(select(Domain).where(Domain.slug == domain_slug))
    ).scalar_one_or_none()
    if domain is None:
        raise ValueError("Domain not found.")

    existing = (
        await db.execute(
            select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.domain_id == domain.id,
                UserSubscription.status == "active",
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ValueError("You already have an active subscription for this domain.")

    sub = UserSubscription(
        user_id=user_id,
        plan_id=plan.id,
        domain_id=domain.id,
        plan_months=plan.plan_months,
        status="active",
        started_at=_now(),
        expires_at=_now() + timedelta(days=plan.plan_months * 30),
    )
    db.add(sub)
    await db.flush()

    await generate_roadmap(db, user_id, domain.id, plan.plan_months, sub.id)
    sub.roadmap_generated = True

    await db.commit()
    await db.refresh(sub)
    return sub


async def generate_roadmap(
    db: AsyncSession, user_id: str, domain_id: str, plan_months: int, subscription_id: str
) -> int:
    """Write user_topic_progress rows for every unlocked topic. Returns count created."""
    # phases unlocked by the plan length
    phases = (
        await db.execute(
            select(DomainPhase)
            .where(DomainPhase.domain_id == domain_id, DomainPhase.min_plan_months <= plan_months)
            .order_by(DomainPhase.order_index)
        )
    ).scalars().all()
    phase_ids = [p.id for p in phases]
    if not phase_ids:
        return 0

    topics = (
        await db.execute(
            select(RoadmapTopic)
            .where(RoadmapTopic.domain_id == domain_id, RoadmapTopic.phase_id.in_(phase_ids))
            .order_by(RoadmapTopic.order_index)
        )
    ).scalars().all()

    # keep the phase order (order_index) as the primary sort
    phase_order = {p.id: p.order_index for p in phases}
    topics = sorted(topics, key=lambda t: (phase_order.get(t.phase_id, 0), t.order_index))

    # skip topics that already have progress for this user (idempotent)
    existing_topic_ids = set(
        (
            await db.execute(
                select(UserTopicProgress.topic_id).where(UserTopicProgress.user_id == user_id)
            )
        ).scalars().all()
    )

    created = 0
    first = True
    for t in topics:
        if t.id in existing_topic_ids:
            continue
        row = UserTopicProgress(
            user_id=user_id,
            topic_id=t.id,
            subscription_id=subscription_id,
            status="current" if first else "not_started",
            started_at=_now() if first else None,
        )
        db.add(row)
        created += 1
        first = False

    await db.flush()
    return created


async def get_roadmap(db: AsyncSession, user_id: str, subscription_id: str) -> list[dict]:
    """Return ordered roadmap items: topic + phase name + progress status/mastery."""
    rows = (
        await db.execute(
            select(UserTopicProgress, RoadmapTopic, DomainPhase.name, DomainPhase.order_index)
            .join(RoadmapTopic, UserTopicProgress.topic_id == RoadmapTopic.id)
            .join(DomainPhase, RoadmapTopic.phase_id == DomainPhase.id)
            .where(
                UserTopicProgress.user_id == user_id,
                UserTopicProgress.subscription_id == subscription_id,
            )
            .order_by(DomainPhase.order_index, RoadmapTopic.order_index)
        )
    ).all()

    return [
        {
            "topic_id": topic.id,
            "title": topic.title,
            "slug": topic.slug,
            "skill_category": topic.skill_category,
            "phase_name": phase_name,
            "order_index": topic.order_index,
            "status": utp.status,
            "mastery_score": utp.mastery_score,
            "questions_completed": utp.questions_completed,
        }
        for (utp, topic, phase_name, _phase_order) in rows
    ]


__all__ = ["subscribe", "generate_roadmap", "get_roadmap", "get_active_subscription"]
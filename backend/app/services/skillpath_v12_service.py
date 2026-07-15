# backend/app/services/skillpath_v12_service.py
"""
ATLAS AI 4.0 - v12 SkillPath Reforged: domain-first flow + roadmap.

Type A throughout - ZERO AI calls. Everything here is registry lookups,
idempotent seeding of the shared library skeleton, and pure progress math.

Flow implemented (v12 spec Section 2, steps 1-3):
  1. list_domains()            -> the nine locked domain cards
  2. select_domain_and_plan()  -> domain FIRST, then plan; upserts the
                                  student's active subscription state
  3. get_roadmap()             -> ordered topic cards with progress ring,
                                  status color and est hours

Status math (deterministic, locked):
  * ring pct   = mastered_subtopics / subtopic_total * 100
  * complete   = ring == 100                              (green)
  * locked     = phase gated by plan OR a previous topic
                 in the walk order is not complete        (grey)
  * current    = the first unlocked, incomplete topic     (blue)
"""

import json
import re
from typing import Dict, List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import Domain, RoadmapTopic
from app.models.plan import SubscriptionPlan, UserSubscription
from app.models.skill_progress import UserTopicProgress
from app.models.skillpath_v12 import DomainRoadmapItem
from app.services.curriculum_registry import (
    DOMAIN_ORDER,
    DOMAIN_REGISTRY,
    TOPIC_LIBRARY,
    MASTERY_CORRECT_THRESHOLD,
    domain_stats,
    phase_unlocked,
)


# ----------------------------------------------------------------------
# Step 1 - the nine domain cards
# ----------------------------------------------------------------------

async def list_domains(db: AsyncSession) -> List[dict]:
    """Nine cards, registry order. Attaches the DB id when registered."""
    rows = (await db.execute(select(Domain))).scalars().all()
    by_key: Dict[str, Domain] = {d.slug: d for d in rows if getattr(d, "slug", None)}

    cards: List[dict] = []
    for key in DOMAIN_ORDER:
        spec = DOMAIN_REGISTRY[key]
        stats = domain_stats(key)
        db_row = by_key.get(key)
        cards.append({
            "domain_id": db_row.id if db_row else None,
            "key": key,
            "name": spec["name"],
            "tagline": spec["tagline"],
            "roles": spec["roles"],
            "example_companies": spec["example_companies"],
            **stats,
        })
    return cards


# ----------------------------------------------------------------------
# Idempotent registration of the shared library skeleton
# ----------------------------------------------------------------------
# Topics live ONCE in roadmap_topics (domain_id NULL = shared library);
# domain_roadmap_items points a domain at them in the founder's order.
# Safe to call on every select - it only creates what is missing.

def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


async def _get_or_create_library_topic(
    db: AsyncSession, topic_key: str
) -> RoadmapTopic:
    spec = TOPIC_LIBRARY[topic_key]
    q = select(RoadmapTopic).where(
        RoadmapTopic.title == spec["title"],
        RoadmapTopic.parent_topic_id.is_(None),
    )
    topic = (await db.execute(q)).scalars().first()
    if topic is None:
        topic = RoadmapTopic(
            title=spec["title"], slug=_slugify(spec["title"]), parent_topic_id=None,
        )
        db.add(topic)
        await db.flush()
        # subtopic tree, founder's order
        for i, name in enumerate(spec["subtopics"]):
            db.add(RoadmapTopic(
                title=name, slug=_slugify(name), parent_topic_id=topic.id, item_order=i,
            ))
        await db.flush()
    return topic


async def ensure_domain_registered(db: AsyncSession, domain_key: str) -> Domain:
    if domain_key not in DOMAIN_REGISTRY:
        raise ValueError(f"Unknown domain key: {domain_key}")
    spec = DOMAIN_REGISTRY[domain_key]

    domain = (
        await db.execute(select(Domain).where(Domain.slug == domain_key))
    ).scalars().first()
    if domain is None:
        domain = Domain(slug=domain_key, name=spec["name"])
        db.add(domain)
        await db.flush()

    existing = (
        await db.execute(
            select(DomainRoadmapItem).where(
                DomainRoadmapItem.domain_id == domain.id
            )
        )
    ).scalars().all()
    have_topic_ids = {it.topic_id for it in existing}

    for order, entry in enumerate(spec["roadmap"]):
        topic = await _get_or_create_library_topic(db, entry["topic_key"])
        if topic.id not in have_topic_ids:
            db.add(DomainRoadmapItem(
                domain_id=domain.id,
                topic_id=topic.id,
                item_order=order,
                phase=entry["phase"],
                est_hours=TOPIC_LIBRARY[entry["topic_key"]]["est_hours"],
            ))
    await db.flush()
    return domain


# ----------------------------------------------------------------------
# Step 2 - select domain, THEN plan
# ----------------------------------------------------------------------

async def _get_or_create_plan(db: AsyncSession, plan_months: int) -> SubscriptionPlan:
    plan = (
        await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.plan_months == plan_months)
        )
    ).scalars().first()
    if plan is None:
        plan = SubscriptionPlan(
            name=f"{plan_months}-Month Career Track",
            slug=f"plan-{plan_months}m",
            plan_months=plan_months,
        )
        db.add(plan)
        await db.flush()
    return plan


async def select_domain_and_plan(
    db: AsyncSession, user_id: str, domain_key: str, plan_months: int
) -> dict:
    if plan_months not in (3, 6, 9):
        raise ValueError("plan_months must be 3, 6 or 9")

    domain = await ensure_domain_registered(db, domain_key)
    plan = await _get_or_create_plan(db, plan_months)

    sub = (
        await db.execute(
            select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.domain_id == domain.id,
            )
        )
    ).scalars().first()
    if sub is None:
        sub = UserSubscription(
            user_id=user_id, domain_id=domain.id, plan_id=plan.id,
            plan_months=plan_months, status="active",
        )
        db.add(sub)
    else:
        sub.plan_id = plan.id
        sub.plan_months = plan_months
        sub.status = "active"
    await db.commit()

    return {
        "domain_id": domain.id,
        "domain_key": domain_key,
        "plan_months": plan_months,
        "roadmap_ready": True,
    }


async def get_active_plan_months(
    db: AsyncSession, user_id: str, domain_id: str
) -> int:
    sub = (
        await db.execute(
            select(UserSubscription).where(
                UserSubscription.user_id == user_id,
                UserSubscription.domain_id == domain_id,
                UserSubscription.status == "active",
            )
        )
    ).scalars().first()
    return int(sub.plan_months) if sub else 3


# ----------------------------------------------------------------------
# Progress math (pure, deterministic - shared with practice service)
# ----------------------------------------------------------------------

def round_half_up(x: float) -> int:
    """Deterministic half-up rounding (avoids banker's rounding: 12.5 -> 13)."""
    return int(x + 0.5)


def parse_progress_json(raw: Optional[str]) -> dict:
    """UTP.progress_json uses underscore-prefixed keys, per convention:
    {"_seen_qids": [...], "_answered": n, "_correct": n, "_score_sum": n}"""
    if not raw:
        return {"_seen_qids": [], "_answered": 0, "_correct": 0, "_score_sum": 0}
    try:
        data = json.loads(raw) if isinstance(raw, str) else dict(raw)
    except (ValueError, TypeError):
        data = {}
    data.setdefault("_seen_qids", [])
    data.setdefault("_answered", 0)
    data.setdefault("_correct", 0)
    data.setdefault("_score_sum", 0)
    return data


def is_mastered(correct_count: int) -> bool:
    return correct_count >= MASTERY_CORRECT_THRESHOLD


async def _subtopic_mastery_map(
    db: AsyncSession, user_id: str, domain_id: str
) -> Dict[str, Tuple[int, int]]:
    """subtopic_topic_id -> (answered, correct) for this user IN this domain."""
    rows = (
        await db.execute(
            select(UserTopicProgress).where(
                UserTopicProgress.user_id == user_id,
                UserTopicProgress.domain_id == domain_id,
            )
        )
    ).scalars().all()
    out: Dict[str, Tuple[int, int]] = {}
    for r in rows:
        p = parse_progress_json(getattr(r, "progress_json", None))
        out[r.topic_id] = (int(p["_answered"]), int(p["_correct"]))
    return out


# ----------------------------------------------------------------------
# Step 3 - the roadmap with progress rings + status colors
# ----------------------------------------------------------------------

async def get_roadmap(db: AsyncSession, user_id: str, domain_id: str) -> dict:
    domain = (
        await db.execute(select(Domain).where(Domain.id == domain_id))
    ).scalars().first()
    if domain is None:
        raise ValueError("Domain not found")

    plan_months = await get_active_plan_months(db, user_id, domain_id)
    items = (
        await db.execute(
            select(DomainRoadmapItem)
            .where(DomainRoadmapItem.domain_id == domain_id)
            .order_by(DomainRoadmapItem.item_order)
        )
    ).scalars().all()

    mastery = await _subtopic_mastery_map(db, user_id, domain_id)

    cards: List[dict] = []
    for item in items:
        topic = (
            await db.execute(
                select(RoadmapTopic).where(RoadmapTopic.id == item.topic_id)
            )
        ).scalars().first()
        subtopics = (
            await db.execute(
                select(RoadmapTopic)
                .where(RoadmapTopic.parent_topic_id == item.topic_id)
                .order_by(RoadmapTopic.item_order)
            )
        ).scalars().all()

        total = max(len(subtopics), 1)
        mastered = sum(
            1 for st in subtopics if is_mastered(mastery.get(st.id, (0, 0))[1])
        )
        pct = round_half_up(mastered / total * 100)

        spec_key = _topic_key_by_title(topic.title)
        cards.append({
            "topic_id": topic.id,
            "title": topic.title,
            "item_order": item.item_order,
            "phase": item.phase,
            "est_hours": item.est_hours,
            "subtopic_total": len(subtopics),
            "subtopics_mastered": mastered,
            "progress_pct": pct,
            "status": "pending",         # resolved in the pass below
            "_phase_open": phase_unlocked(item.phase, plan_months),
            "viz_kind": TOPIC_LIBRARY[spec_key]["viz_kind"] if spec_key else "chart_viz",
        })

    # Status pass: walk order + plan gate. First unlocked incomplete = current.
    current_assigned = False
    for card in cards:
        if card["progress_pct"] == 100:
            card["status"] = "complete"
        elif not card["_phase_open"]:
            card["status"] = "locked"
        elif not current_assigned:
            card["status"] = "current"
            current_assigned = True
        else:
            card["status"] = "locked"
        card.pop("_phase_open")

    overall = round_half_up(sum(c["progress_pct"] for c in cards) / max(len(cards), 1))
    return {
        "domain_id": domain_id,
        "domain_key": domain.slug,
        "domain_name": domain.name,
        "plan_months": plan_months,
        "topics": cards,
        "overall_pct": overall,
    }


def _topic_key_by_title(title: str) -> Optional[str]:
    for key, spec in TOPIC_LIBRARY.items():
        if spec["title"] == title:
            return key
    return None

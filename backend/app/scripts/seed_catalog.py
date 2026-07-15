# backend/app/scripts/seed_catalog.py
"""
Seed the shared catalogue: 7 career domains (each with 4 phases), the 3 plan
tiers, and a starter set of Data Science topics so the roadmap has content to
show. Idempotent — safe to run repeatedly (keys on slug).

Run:
    python -m app.scripts.seed_catalog
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.domain import Domain, DomainPhase, RoadmapTopic
from app.models.plan import SubscriptionPlan

# (slug, name, icon)
DOMAINS = [
    ("data_science", "Data Science", "chart"),
    ("software_engineer", "Software Engineer", "code"),
    ("web_development", "Web Development", "globe"),
    ("machine_learning", "Machine Learning", "brain"),
    ("data_analyst", "Data Analyst", "table"),
    ("cloud_devops", "Cloud & DevOps", "cloud"),
    ("cybersecurity", "Cybersecurity", "shield"),
]

# (name, min_plan_months, order_index)
PHASES = [
    ("Foundation", 3, 0),
    ("Core", 3, 1),
    ("Advanced", 6, 2),
    ("Capstone", 9, 3),
]

# (slug, name, plan_months, price_inr, description)
PLANS = [
    ("plan-3m", "3-Month Kickstart", 3, 447, "Foundation + Core phases"),
    ("plan-6m", "6-Month Career Track", 6, 794, "Adds the Advanced phase"),
    ("plan-9m", "9-Month Placement Pro", 9, 1341, "Full roadmap incl. Capstone"),
]

# Starter Data Science topics for the Foundation phase (top-level).
DS_FOUNDATION_TOPICS = [
    ("Python", "python", "Python"),
    ("NumPy", "numpy", "Python"),
    ("Pandas", "pandas", "Data Wrangling"),
    ("Statistics", "statistics", "Math"),
]


async def _seed_domains(db) -> dict:
    out: dict = {}
    for order, (slug, name, icon) in enumerate(DOMAINS):
        dom = (await db.execute(select(Domain).where(Domain.slug == slug))).scalar_one_or_none()
        if dom is None:
            dom = Domain(slug=slug, name=name, icon=icon, order_index=order,
                         description=f"Placement track for {name}.")
            db.add(dom)
            await db.flush()
        out[slug] = dom

        existing_phases = {
            p.name for p in (
                await db.execute(select(DomainPhase).where(DomainPhase.domain_id == dom.id))
            ).scalars().all()
        }
        for pname, min_m, pidx in PHASES:
            if pname not in existing_phases:
                db.add(DomainPhase(domain_id=dom.id, name=pname, min_plan_months=min_m, order_index=pidx))
        await db.flush()
    return out


async def _seed_plans(db) -> None:
    for slug, name, months, price, desc in PLANS:
        exists = (await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.slug == slug))).scalar_one_or_none()
        if exists is None:
            db.add(SubscriptionPlan(slug=slug, name=name, plan_months=months,
                                    price_inr=price, description=desc))
    await db.flush()


async def _seed_ds_topics(db, ds: Domain) -> None:
    foundation = (
        await db.execute(
            select(DomainPhase).where(
                DomainPhase.domain_id == ds.id, DomainPhase.name == "Foundation"
            )
        )
    ).scalar_one_or_none()
    if foundation is None:
        return
    for order, (title, slug, skill) in enumerate(DS_FOUNDATION_TOPICS):
        exists = (
            await db.execute(
                select(RoadmapTopic).where(
                    RoadmapTopic.domain_id == ds.id, RoadmapTopic.slug == slug
                )
            )
        ).scalar_one_or_none()
        if exists is None:
            db.add(RoadmapTopic(
                domain_id=ds.id, phase_id=foundation.id, title=title, slug=slug,
                skill_category=skill, order_index=order, estimated_hours=6,
            ))
    await db.flush()


async def main() -> None:
    async with AsyncSessionLocal() as db:
        domains = await _seed_domains(db)
        await _seed_plans(db)
        await _seed_ds_topics(db, domains["data_science"])
        await db.commit()
    print("Seeded: 7 domains x 4 phases, 3 plans, Data Science Foundation topics.")


if __name__ == "__main__":
    asyncio.run(main())
# FILE: backend/app/scripts/seed_subtopics.py
"""
v12 — creates the child roadmap_topics rows (subtopics) that SkillPath 3.0 assumes exist.

Source of truth = content_library.subtopics_json (already seeded), mapped into domains
via domain_topic_map. For each shared module, finds the matching parent topic in that
domain and creates its child subtopic rows.

Idempotent (skips existing). NO AI calls.
Run BEFORE seed_domain_learn_cards and seed_practice_questions.

Run:  python -m app.scripts.seed_subtopics
"""
import asyncio
import re

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.domain import RoadmapTopic
from app.models.content_library import ContentLibrary, DomainTopicMap


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


async def main():
    async with AsyncSessionLocal() as db:
        mappings = (
            await db.execute(
                select(DomainTopicMap, ContentLibrary).join(
                    ContentLibrary, DomainTopicMap.content_module_id == ContentLibrary.id
                )
            )
        ).all()

        created = 0
        for mapping, module in mappings:
            parent = (
                await db.execute(
                    select(RoadmapTopic).where(
                        RoadmapTopic.domain_id == mapping.domain_id,
                        RoadmapTopic.parent_topic_id.is_(None),
                        RoadmapTopic.title == module.title,
                    )
                )
            ).scalars().first()

            if parent is None:
                print(f"[skip] no parent topic titled '{module.title}' in domain {mapping.domain_id}")
                continue

            existing = {
                t.title
                for t in (
                    await db.execute(
                        select(RoadmapTopic).where(RoadmapTopic.parent_topic_id == parent.id)
                    )
                ).scalars().all()
            }

            for item in (module.subtopics_json or []):
                name = item.get("name") if isinstance(item, dict) else str(item)
                order = item.get("order", 1) if isinstance(item, dict) else 1
                if not name or name in existing:
                    continue

                db.add(
                    RoadmapTopic(
                        domain_id=parent.domain_id,
                        phase_id=parent.phase_id,
                        parent_topic_id=parent.id,
                        title=name,
                        slug=slugify(f"{module.module_key}-{name}"),
                        skill_category=getattr(parent, "skill_category", None),
                        order_index=order,
                        estimated_hours=2,
                    )
                )
                created += 1
                print(f"[ok] subtopic: {module.title} / {name}")

        await db.commit()
        print(f"seed_subtopics: {created} subtopics created")


if __name__ == "__main__":
    asyncio.run(main())
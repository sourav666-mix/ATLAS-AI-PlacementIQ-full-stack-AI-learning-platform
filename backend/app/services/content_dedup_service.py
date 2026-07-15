# backend/app/services/content_dedup_service.py   [NEW v12]
"""
ATLAS AI 4.0 (v12) — resolves content_library -> domain_topic_map.

This is the de-duplication layer: the 5 shared modules are authored once in
content_library; every domain that should show a module gets a row in
domain_topic_map. Editing the shared row updates every mapped domain with no re-seed.

Type A only. Pure DB reads/writes — zero AI calls.
"""
from typing import List, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_library import ContentLibrary, DomainTopicMap


async def get_shared_module(db: AsyncSession, module_key: str) -> Optional[ContentLibrary]:
    """Fetch one shared module by its key (e.g. 'python')."""
    res = await db.execute(
        select(ContentLibrary).where(ContentLibrary.module_key == module_key)
    )
    return res.scalar_one_or_none()


async def resolve_domain_modules(db: AsyncSession, domain_id: str) -> List[Dict[str, Any]]:
    """
    Return the shared modules a domain displays, in display_order.
    Each item: {content_module_id, module_key, title, subtopics_json, display_order}.
    """
    stmt = (
        select(DomainTopicMap, ContentLibrary)
        .join(ContentLibrary, DomainTopicMap.content_module_id == ContentLibrary.id)
        .where(DomainTopicMap.domain_id == domain_id)
        .order_by(DomainTopicMap.display_order.asc())
    )
    rows = (await db.execute(stmt)).all()
    resolved: List[Dict[str, Any]] = []
    for mapping, module in rows:
        resolved.append(
            {
                "content_module_id": module.id,
                "module_key": module.module_key,
                "title": module.title,
                "subtopics_json": module.subtopics_json or [],
                "display_order": mapping.display_order,
            }
        )
    return resolved


async def map_module_into_domain(
    db: AsyncSession,
    domain_id: str,
    module_key: str,
    display_order: int,
) -> DomainTopicMap:
    """
    Idempotent upsert used by seed_content_library.py. If the (domain, module) pair
    already exists, only the display_order is refreshed — never a duplicate row.
    """
    module = await get_shared_module(db, module_key)
    if module is None:
        raise ValueError(f"content_library module '{module_key}' not found — seed it first")

    existing = (
        await db.execute(
            select(DomainTopicMap).where(
                DomainTopicMap.domain_id == domain_id,
                DomainTopicMap.content_module_id == module.id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.display_order = display_order
        mapping = existing
    else:
        mapping = DomainTopicMap(
            domain_id=domain_id,
            content_module_id=module.id,
            display_order=display_order,
        )
        db.add(mapping)

    await db.flush()
    return mapping
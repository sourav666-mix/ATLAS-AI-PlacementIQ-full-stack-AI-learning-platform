# FILE: app/services/content_admin_service.py
# BATCH 16 (new) - Curriculum CRUD: domains -> phases -> topics -> subtopics
# (subtopic = roadmap_topics row with parent_topic_id set, per the v10 ALTER)
# plus the topic concept card (topic_content). Pure DB work — zero AI (Type A).
#
# Tables (v10 schema): domains, domain_phases, roadmap_topics, topic_content.
# All writes are audited via admin_common.audit().

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.admin_common import (
    apply_fields, audit, col, column_names, require_model, row_get, to_dict,
)

T_DOMAINS = "domains"
T_PHASES = "domain_phases"
T_TOPICS = "roadmap_topics"
T_CONTENT = "topic_content"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _order_col(model):
    return col(model, "sort_order", "order_index", "position", "seq", "order_no")


def _name_col(model):
    return col(model, "name", "title", "label")


async def _get_or_404(db: AsyncSession, model, row_id: str, what: str):
    row = await db.get(model, row_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"{what} '{row_id}' not found")
    return row


def _new_row(model, payload: dict):
    row = model()
    cols = column_names(model)
    if "id" in cols and not payload.get("id"):
        payload = {**payload, "id": str(uuid.uuid4())}
    apply_fields(row, payload)
    return row


async def _count_children(db: AsyncSession, child_model, fk_names, parent_id) -> int:
    fk = col(child_model, *fk_names)
    if fk is None:
        return 0
    res = await db.execute(select(func.count()).where(fk == parent_id))
    return int(res.scalar() or 0)


# ---------------------------------------------------------------------------
# DOMAINS
# ---------------------------------------------------------------------------
async def list_domains(db: AsyncSession) -> list:
    Domain = require_model(T_DOMAINS)
    order = _order_col(Domain) or _name_col(Domain)
    stmt = select(Domain)
    if order is not None:
        stmt = stmt.order_by(order)
    rows = (await db.execute(stmt)).scalars().all()
    Topic = require_model(T_TOPICS)
    out = []
    for row in rows:
        d = to_dict(row)
        d["topic_count"] = await _count_children(
            db, Topic, ("domain_id",), row_get(row, "id"))
        out.append(d)
    return out


async def create_domain(db: AsyncSession, admin, payload: dict) -> dict:
    Domain = require_model(T_DOMAINS)
    row = _new_row(Domain, payload)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    await audit(db, admin, "content.create_domain", T_DOMAINS,
                row_get(row, "id"), payload)
    return to_dict(row)


async def update_domain(db: AsyncSession, admin, domain_id: str, payload: dict) -> dict:
    Domain = require_model(T_DOMAINS)
    row = await _get_or_404(db, Domain, domain_id, "Domain")
    applied = apply_fields(row, payload)
    await db.commit()
    await db.refresh(row)
    await audit(db, admin, "content.update_domain", T_DOMAINS, domain_id, applied)
    return to_dict(row)


async def delete_domain(db: AsyncSession, admin, domain_id: str) -> dict:
    Domain = require_model(T_DOMAINS)
    Topic = require_model(T_TOPICS)
    row = await _get_or_404(db, Domain, domain_id, "Domain")
    n = await _count_children(db, Topic, ("domain_id",), domain_id)
    if n > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Domain has {n} topics. Delete or move them first.")
    await db.delete(row)
    await db.commit()
    await audit(db, admin, "content.delete_domain", T_DOMAINS, domain_id)
    return {"deleted": domain_id}


# ---------------------------------------------------------------------------
# PHASES
# ---------------------------------------------------------------------------
async def list_phases(db: AsyncSession, domain_id: Optional[str] = None) -> list:
    Phase = require_model(T_PHASES)
    stmt = select(Phase)
    fk = col(Phase, "domain_id")
    if domain_id and fk is not None:
        stmt = stmt.where(fk == domain_id)
    order = _order_col(Phase)
    if order is not None:
        stmt = stmt.order_by(order)
    return [to_dict(r) for r in (await db.execute(stmt)).scalars().all()]


async def create_phase(db: AsyncSession, admin, payload: dict) -> dict:
    Phase = require_model(T_PHASES)
    row = _new_row(Phase, payload)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    await audit(db, admin, "content.create_phase", T_PHASES,
                row_get(row, "id"), payload)
    return to_dict(row)


async def update_phase(db: AsyncSession, admin, phase_id: str, payload: dict) -> dict:
    Phase = require_model(T_PHASES)
    row = await _get_or_404(db, Phase, phase_id, "Phase")
    applied = apply_fields(row, payload)
    await db.commit()
    await db.refresh(row)
    await audit(db, admin, "content.update_phase", T_PHASES, phase_id, applied)
    return to_dict(row)


async def delete_phase(db: AsyncSession, admin, phase_id: str) -> dict:
    Phase = require_model(T_PHASES)
    Topic = require_model(T_TOPICS)
    row = await _get_or_404(db, Phase, phase_id, "Phase")
    n = await _count_children(db, Topic, ("phase_id", "domain_phase_id"), phase_id)
    if n > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Phase has {n} topics. Delete or move them first.")
    await db.delete(row)
    await db.commit()
    await audit(db, admin, "content.delete_phase", T_PHASES, phase_id)
    return {"deleted": phase_id}


# ---------------------------------------------------------------------------
# TOPICS + SUBTOPICS (parent_topic_id tree)
# ---------------------------------------------------------------------------
async def list_topics(db: AsyncSession,
                      domain_id: Optional[str] = None,
                      phase_id: Optional[str] = None,
                      parent_id: Optional[str] = None,
                      top_level_only: bool = False) -> list:
    Topic = require_model(T_TOPICS)
    stmt = select(Topic)
    dfk = col(Topic, "domain_id")
    pfk = col(Topic, "phase_id", "domain_phase_id")
    parent = col(Topic, "parent_topic_id", "parent_id")
    if domain_id and dfk is not None:
        stmt = stmt.where(dfk == domain_id)
    if phase_id and pfk is not None:
        stmt = stmt.where(pfk == phase_id)
    if parent is not None:
        if parent_id:
            stmt = stmt.where(parent == parent_id)
        elif top_level_only:
            stmt = stmt.where(parent.is_(None))
    order = _order_col(Topic)
    if order is not None:
        stmt = stmt.order_by(order)
    return [to_dict(r) for r in (await db.execute(stmt)).scalars().all()]


async def create_topic(db: AsyncSession, admin, payload: dict) -> dict:
    """Create a topic OR a subtopic (pass parent_topic_id for a subtopic)."""
    Topic = require_model(T_TOPICS)
    row = _new_row(Topic, payload)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    action = ("content.create_subtopic"
              if payload.get("parent_topic_id") or payload.get("parent_id")
              else "content.create_topic")
    await audit(db, admin, action, T_TOPICS, row_get(row, "id"), payload)
    return to_dict(row)


async def update_topic(db: AsyncSession, admin, topic_id: str, payload: dict) -> dict:
    Topic = require_model(T_TOPICS)
    row = await _get_or_404(db, Topic, topic_id, "Topic")
    applied = apply_fields(row, payload)
    await db.commit()
    await db.refresh(row)
    await audit(db, admin, "content.update_topic", T_TOPICS, topic_id, applied)
    return to_dict(row)


async def delete_topic(db: AsyncSession, admin, topic_id: str) -> dict:
    Topic = require_model(T_TOPICS)
    row = await _get_or_404(db, Topic, topic_id, "Topic")
    n = await _count_children(db, Topic, ("parent_topic_id", "parent_id"), topic_id)
    if n > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Topic has {n} subtopics. Delete them first.")
    await db.delete(row)
    await db.commit()
    await audit(db, admin, "content.delete_topic", T_TOPICS, topic_id)
    return {"deleted": topic_id}


async def reorder_topics(db: AsyncSession, admin, items: list) -> dict:
    """items = [{id, sort_order}]. Works for topics, subtopics and phases-in-topic order."""
    Topic = require_model(T_TOPICS)
    order_name = None
    for candidate in ("sort_order", "order_index", "position", "seq", "order_no"):
        if candidate in column_names(Topic):
            order_name = candidate
            break
    if order_name is None:
        raise HTTPException(status_code=500,
                            detail="roadmap_topics has no sort/order column")
    updated = 0
    for item in items:
        row = await db.get(Topic, item["id"])
        if row is not None:
            setattr(row, order_name, int(item["sort_order"]))
            updated += 1
    await db.commit()
    await audit(db, admin, "content.reorder_topics", T_TOPICS, None,
                {"count": updated})
    return {"updated": updated}


# ---------------------------------------------------------------------------
# CONCEPT CARD (topic_content) — what / how / why + 4 worked examples
# ---------------------------------------------------------------------------
async def get_topic_content(db: AsyncSession, topic_id: str) -> dict:
    Content = require_model(T_CONTENT)
    fk = col(Content, "topic_id")
    if fk is None:
        raise HTTPException(status_code=500,
                            detail="topic_content has no topic_id column")
    row = (await db.execute(select(Content).where(fk == topic_id))
           ).scalars().first()
    return to_dict(row) if row is not None else {"topic_id": topic_id, "exists": False}


async def upsert_topic_content(db: AsyncSession, admin,
                               topic_id: str, payload: dict) -> dict:
    Content = require_model(T_CONTENT)
    fk = col(Content, "topic_id")
    if fk is None:
        raise HTTPException(status_code=500,
                            detail="topic_content has no topic_id column")
    row = (await db.execute(select(Content).where(fk == topic_id))
           ).scalars().first()
    payload = {**payload, "topic_id": topic_id}
    if row is None:
        row = _new_row(Content, payload)
        db.add(row)
        action = "content.create_topic_content"
    else:
        apply_fields(row, payload)
        action = "content.update_topic_content"
    await db.commit()
    await db.refresh(row)
    await audit(db, admin, action, T_CONTENT, row_get(row, "id"),
                {"topic_id": topic_id, "fields": sorted(payload.keys())})
    return to_dict(row)


# ---------------------------------------------------------------------------
# FULL TREE — one call for the admin ContentManagement screen
# ---------------------------------------------------------------------------
async def content_tree(db: AsyncSession) -> list:
    domains = await list_domains(db)
    Topic = require_model(T_TOPICS)
    parent = col(Topic, "parent_topic_id", "parent_id")
    for domain in domains:
        did = domain.get("id")
        domain["phases"] = await list_phases(db, domain_id=did)
        topics = await list_topics(db, domain_id=did,
                                   top_level_only=parent is not None)
        by_id = {t.get("id"): t for t in topics}
        for topic in topics:
            topic["subtopics"] = (await list_topics(db, parent_id=topic.get("id"))
                                  if parent is not None else [])
        # attach topics under their phase when phase_id exists, else flat
        for phase in domain["phases"]:
            pid = phase.get("id")
            phase["topics"] = [t for t in topics
                               if t.get("phase_id") == pid
                               or t.get("domain_phase_id") == pid]
        domain["topics"] = topics if not domain["phases"] else \
            [t for t in topics if not (t.get("phase_id") or t.get("domain_phase_id"))]
        _ = by_id  # reserved for future cross-links
    return domains
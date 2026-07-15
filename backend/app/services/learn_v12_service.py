# backend/app/services/learn_v12_service.py
"""
ATLAS AI 4.0 - v12 SkillPath Reforged: LEARN mode (spec Section 2, step 4).

Type A - ZERO AI calls. Learn content is seeded once (seed_content.py,
session V12-6) into topic_content and served verbatim from MySQL.

Per subtopic, the explainer is LOCKED at:
  what_it_is / when_to_use / how_to_use / exactly FIVE worked examples.

topic_content.body_json layout (written by the seeder):
{
  "_what": "...", "_when": "...", "_how": "...",
  "_examples": [ {title, code, output, why} x5 ]
}
Underscore-prefixed keys per platform convention for JSON state columns.

If a subtopic has not been seeded yet, we return a deterministic
placeholder (never a live AI generation at request time - that would
break the cost model).
"""

import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import RoadmapTopic
from app.models.practice import TopicContent
from app.services.curriculum_registry import TOPIC_LIBRARY

LEARN_EXAMPLE_COUNT = 5   # locked at five (v12 spec, Section 2 step 4)


def _placeholder_examples(name: str) -> List[dict]:
    return [
        {
            "title": f"{name} - example {i + 1} (content pending seed)",
            "code": "# seeded content arrives with scripts/seed_content.py",
            "output": "",
            "why": "This subtopic's explainer has not been seeded yet.",
        }
        for i in range(LEARN_EXAMPLE_COUNT)
    ]


def _parse_body(raw) -> Optional[dict]:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return None


def _normalize_examples(examples: List[dict]) -> List[dict]:
    """Serve exactly five: pad deterministically, never truncate silently
    below five, cap at five."""
    fixed = []
    for ex in examples[:LEARN_EXAMPLE_COUNT]:
        fixed.append({
            "title": str(ex.get("title", "Example")),
            "code": str(ex.get("code", "")),
            "output": str(ex.get("output", "")),
            "why": str(ex.get("why", "")),
        })
    while len(fixed) < LEARN_EXAMPLE_COUNT:
        fixed.append({
            "title": f"Example {len(fixed) + 1} (pending seed)",
            "code": "", "output": "",
            "why": "Additional example arrives with the content seed.",
        })
    return fixed


async def get_topic_learn(db: AsyncSession, topic_id: str) -> dict:
    topic = (
        await db.execute(select(RoadmapTopic).where(RoadmapTopic.id == topic_id))
    ).scalars().first()
    if topic is None or topic.parent_topic_id is not None:
        raise ValueError("Topic not found (Learn mode opens parent topics only)")

    subtopics = (
        await db.execute(
            select(RoadmapTopic)
            .where(RoadmapTopic.parent_topic_id == topic_id)
            .order_by(RoadmapTopic.item_order)
        )
    ).scalars().all()

    # one query for all content rows of this topic's subtopics
    content_rows = (
        await db.execute(
            select(TopicContent).where(
                TopicContent.topic_id.in_([st.id for st in subtopics] or ["-"])
            )
        )
    ).scalars().all()
    content_by_subtopic = {c.topic_id: c for c in content_rows}

    # topic-level overview (optional row keyed on the parent topic itself)
    topic_row = (
        await db.execute(
            select(TopicContent).where(TopicContent.topic_id == topic_id)
        )
    ).scalars().first()
    topic_body = _parse_body(getattr(topic_row, "body_json", None)) or {}
    overview = topic_body.get("_what") or (
        f"{topic.title}: full explainer arrives with the content seed. "
        f"Every subtopic below covers what it is, when to use it, how to "
        f"use it, and five worked examples."
    )

    spec_key = next(
        (k for k, s in TOPIC_LIBRARY.items() if s["title"] == topic.title), None
    )
    viz_kind = TOPIC_LIBRARY[spec_key]["viz_kind"] if spec_key else "chart_viz"

    explainers = []
    for st in subtopics:
        body = _parse_body(
            getattr(content_by_subtopic.get(st.id), "body_json", None)
        )
        if body:
            explainers.append({
                "subtopic_id": st.id,
                "name": st.title,
                "what_it_is": str(body.get("_what", "")),
                "when_to_use": str(body.get("_when", "")),
                "how_to_use": str(body.get("_how", "")),
                "examples": _normalize_examples(body.get("_examples", [])),
            })
        else:
            explainers.append({
                "subtopic_id": st.id,
                "name": st.title,
                "what_it_is": f"'{st.title}' explainer pending content seed.",
                "when_to_use": "",
                "how_to_use": "",
                "examples": _placeholder_examples(st.title),
            })

    return {
        "topic_id": topic_id,
        "title": topic.title,
        "overview": overview,
        "viz_kind": viz_kind,
        "subtopics": explainers,
    }

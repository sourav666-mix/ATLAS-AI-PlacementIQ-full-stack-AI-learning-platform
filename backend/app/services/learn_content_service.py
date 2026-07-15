# backend/app/services/learn_content_service.py   [NEW v12]
"""
ATLAS AI 4.0 (v12) — serves Learn Card blocks (what / when / how / 5 examples / viz).

THE LAW (v10 Section 5, restated for v12): this file NEVER calls a live AI provider.
Every field here was authored at seed time (Type A) and is read straight from
roadmap_topics. If a Learn Card is weak, fix it in seed_domain_learn_cards.py and
re-seed — do not patch content with a live call.
"""
from typing import List, Dict, Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import RoadmapTopic
from app.models.skillpath_v3 import SubtopicProgress


def _coerce_examples(raw: Any) -> List[Dict[str, str]]:
    """Normalise stored examples_json into [{prompt, solution}] shape (max 5)."""
    out: List[Dict[str, str]] = []
    for item in (raw or [])[:5]:
        if isinstance(item, dict):
            out.append(
                {
                    "prompt": str(item.get("prompt", item.get("input", ""))),
                    "solution": str(item.get("solution", item.get("output", ""))),
                }
            )
    return out


async def get_learn_card(db: AsyncSession, subtopic_id: str) -> Dict[str, Any]:
    """Read the Learn Card for one subtopic. 404 if the subtopic is missing."""
    topic = (
        await db.execute(select(RoadmapTopic).where(RoadmapTopic.id == subtopic_id))
    ).scalar_one_or_none()
    if topic is None:
        raise HTTPException(status_code=404, detail="Subtopic not found")

    return {
        "subtopic_id": topic.id,
        "name": getattr(topic, "title", getattr(topic, "name", "")),
        "what_is_it": topic.what_is_it,
        "when_to_use": topic.when_to_use,
        "how_to_use": topic.how_to_use,
        "examples": _coerce_examples(topic.examples_json),
        "visualization_config": topic.visualization_config_json,
    }


async def get_subtopic_pills(
    db: AsyncSession, user_id: str, topic_id: str
) -> List[Dict[str, Any]]:
    """
    List a topic's child subtopics (roadmap_topics.parent_topic_id == topic_id),
    joined with this student's subtopic_progress to colour the pills. Zero AI.
    """
    subs = (
        await db.execute(
            select(RoadmapTopic)
            .where(RoadmapTopic.parent_topic_id == topic_id)
            .order_by(RoadmapTopic.order_index.asc())
        )
    ).scalars().all()

    prog_rows = (
        await db.execute(
            select(SubtopicProgress).where(SubtopicProgress.user_id == user_id)
        )
    ).scalars().all()
    prog_by_sub = {p.subtopic_id: p for p in prog_rows}

    pills: List[Dict[str, Any]] = []
    for s in subs:
        p = prog_by_sub.get(s.id)
        pills.append(
            {
                "subtopic_id": s.id,
                "name": getattr(s, "title", getattr(s, "name", "")),
                "status": p.status if p else "locked",
                "questions_completed": p.questions_completed if p else 0,
                "mastery_score": p.mastery_score if p else 0,
            }
        )
    return pills
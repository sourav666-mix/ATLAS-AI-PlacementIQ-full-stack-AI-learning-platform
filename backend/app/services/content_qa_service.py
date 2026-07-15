# backend/app/services/content_qa_service.py
"""
ATLAS AI 4.0 - v12 content pipeline: admin QA service.

Type A - ZERO AI calls. The generate-once-cache appends questions with
review_status='auto'; students see them immediately (the bank must never
stall), and admins promote or retire them here:

    approve -> 'published'  (permanent bank member)
    reject  -> 'rejected'   (never served again; the deficit re-opens so
                             the next seeder run replaces it)
"""

import json
from typing import List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import RoadmapTopic
from app.models.practice import TopicQuestion, UserAttempt


async def count_auto_pending(db: AsyncSession) -> int:
    return int((await db.execute(
        select(func.count(TopicQuestion.id)).where(
            TopicQuestion.review_status == "auto")
    )).scalar() or 0)


async def list_auto_questions(
    db: AsyncSession, limit: int = 50
) -> List[dict]:
    rows = (await db.execute(
        select(TopicQuestion)
        .where(TopicQuestion.review_status == "auto")
        .limit(limit)
    )).scalars().all()

    out: List[dict] = []
    for q in rows:
        body = q.body_json if isinstance(q.body_json, dict) \
            else json.loads(q.body_json or "{}")
        subtopic = (await db.execute(select(RoadmapTopic).where(
            RoadmapTopic.id == q.topic_id))).scalars().first()
        parent = None
        if subtopic is not None and subtopic.parent_topic_id:
            parent = (await db.execute(select(RoadmapTopic).where(
                RoadmapTopic.id == subtopic.parent_topic_id))).scalars().first()
        served = int((await db.execute(
            select(func.count(UserAttempt.id)).where(
                UserAttempt.question_id == q.id))).scalar() or 0)
        out.append({
            "question_id": q.id,
            "topic_title": parent.title if parent else "?",
            "subtopic_name": subtopic.title if subtopic else "?",
            "difficulty": q.difficulty or "advanced",
            "question_kind": q.question_kind or "text",
            "question": body.get("question", "")[:2000],
            "model_solution": body.get("model_solution", "")[:3000],
            "times_served": served,
        })
    return out


async def review_question(
    db: AsyncSession, question_id: str, action: str
) -> dict:
    q = (await db.execute(select(TopicQuestion).where(
        TopicQuestion.id == question_id))).scalars().first()
    if q is None:
        raise ValueError("Question not found")
    if q.review_status != "auto":
        raise ValueError("Only review_status='auto' questions can be reviewed")

    q.review_status = "published" if action == "approve" else "rejected"
    await db.commit()
    return {"question_id": question_id, "new_status": q.review_status}
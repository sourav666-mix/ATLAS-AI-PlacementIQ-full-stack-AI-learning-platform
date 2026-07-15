# practice.py - POST /practice/attempt (score) ; /reveal (DB read, no AI)
# backend/app/routers/practice.py
"""
Practice routes (mounted at /practice) — the core learning loop.

    GET  /practice/topics/{topic_id}         -> concept card + questions (no answers)
    GET  /practice/questions/{qid}/reveal    -> stored explanation (PURE DB READ, no AI)
    POST /practice/questions/{qid}/attempt   -> score answer (the one AI call) + award points
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.practice import (
    AttemptIn,
    AttemptResultOut,
    QuestionOut,
    RevealOut,
    TopicContentOut,
)
from app.services import practice_service

router = APIRouter()


@router.get("/topics/{topic_id}", response_model=TopicContentOut)
async def topic_content(topic_id: str, db: AsyncSession = Depends(get_db)):
    content = await practice_service.get_topic_content(db, topic_id)
    questions = await practice_service.list_questions(db, topic_id)
    return TopicContentOut(
        topic_id=topic_id,
        concept_markdown=content.concept_markdown if content else None,
        examples_json=content.examples_json if content else None,
        questions=[QuestionOut.model_validate(q) for q in questions],
    )


@router.get("/questions/{qid}/reveal", response_model=RevealOut)
async def reveal(qid: str, db: AsyncSession = Depends(get_db)):
    try:
        data = await practice_service.reveal_answer(db, qid)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return RevealOut(**data)


@router.post("/questions/{qid}/attempt", response_model=AttemptResultOut)
async def attempt(
    qid: str,
    payload: AttemptIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        result = await practice_service.score_attempt(db, current_user.id, qid, payload.student_answer)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return AttemptResultOut(**result)
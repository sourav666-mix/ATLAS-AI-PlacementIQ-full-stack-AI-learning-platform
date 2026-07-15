# backend/app/routers/admin_content_qa.py
"""
ATLAS AI 4.0 - v12 content pipeline: admin QA router.

Registered on the ADMIN app surface under /admin/content. Uses the
isolated admin JWT dependency (scope=admin, admin_auth subpackage) -
completely separate from student auth, per the locked admin-isolation
convention. All endpoints Type A.
"""

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.admin_auth_service import get_current_admin
from app.schemas.content_qa import (
    AutoQuestionListResponse,
    CoverageResponse,
    ReviewRequest,
    ReviewResponse,
)
from app.services import content_qa_service
from app.scripts.seed_report import build_report

router = APIRouter(prefix="/admin/content", tags=["Admin - Content QA"])


@router.get("/coverage", response_model=CoverageResponse)
async def coverage(
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """Seed coverage per topic + the auto-question review backlog."""
    report = await build_report()
    pending = await content_qa_service.count_auto_pending(db)
    return {**report, "auto_pending": pending}


@router.get("/auto-questions", response_model=AutoQuestionListResponse)
async def auto_questions(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """The generate-once-cache output awaiting human review."""
    questions = await content_qa_service.list_auto_questions(db, limit)
    total = await content_qa_service.count_auto_pending(db)
    return {"questions": questions, "total_pending": total}


@router.post("/auto-questions/{question_id}/review",
             response_model=ReviewResponse)
async def review(
    question_id: str,
    payload: ReviewRequest,
    db: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
):
    """approve -> published (permanent) · reject -> retired forever."""
    try:
        return await content_qa_service.review_question(
            db, question_id, payload.action)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
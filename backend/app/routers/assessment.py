# assessment.py - [MOD] merged mock interview + aptitude + analytics
# backend/app/routers/assessment.py
"""
Assessment Center routes (mounted at /assessment).

    POST /assessment/aptitude/start           -> generate MCQs, start session
    POST /assessment/aptitude/{sid}/submit     -> score (pure math), return breakdown
    POST /assessment/mock/start                -> generate interview questions
    POST /assessment/mock/{sid}/submit         -> AI-evaluate answers, return report
    GET  /assessment/history                   -> past completed sessions (both kinds)
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.assessment import (
    AptitudeResultOut,
    AptitudeStartIn,
    AptitudeStartOut,
    AptitudeSubmitIn,
    AssessmentAnalyticsOut,
    AssessmentHistoryItem,
    MockResultOut,
    MockStartIn,
    MockStartOut,
    MockSubmitIn,
)
from app.services import assessment_service

router = APIRouter()


@router.post("/aptitude/start", response_model=AptitudeStartOut)
async def aptitude_start(
    payload: AptitudeStartIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await assessment_service.start_aptitude(
        db, current_user.id, payload.category, payload.level, payload.count
    )


@router.post("/aptitude/{sid}/submit", response_model=AptitudeResultOut)
async def aptitude_submit(
    sid: str,
    payload: AptitudeSubmitIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await assessment_service.submit_aptitude(db, current_user.id, sid, payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/mock/start", response_model=MockStartOut)
async def mock_start(
    payload: MockStartIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await assessment_service.start_mock(
        db, current_user.id, payload.role, payload.domain, payload.level, payload.count
    )


@router.post("/mock/{sid}/submit", response_model=MockResultOut)
async def mock_submit(
    sid: str,
    payload: MockSubmitIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await assessment_service.submit_mock(db, current_user.id, sid, payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/history", response_model=List[AssessmentHistoryItem])
async def history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await assessment_service.get_history(db, current_user.id, limit)


@router.get("/analytics", response_model=AssessmentAnalyticsOut)
@router.get("/my-analytics", response_model=AssessmentAnalyticsOut)
async def analytics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await assessment_service.get_analytics(db, current_user.id)
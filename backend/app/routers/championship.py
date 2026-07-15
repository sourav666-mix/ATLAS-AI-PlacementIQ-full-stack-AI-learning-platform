# championship.py - [NEW] enter / answer / submit + proctor violation events
# backend/app/routers/championship.py
"""Weekly Championship — student endpoints.

  GET  /championship/live                  -> current live championship (lobby)
  POST /championship/{id}/enter            -> start attempt (returns paper + deadline)
  PUT  /championship/{id}/answer           -> autosave one answer
  POST /championship/{id}/submit           -> final submit
  POST /championship/{id}/violation        -> fullscreen exit event
  GET  /championship/{id}/result           -> result (after closed/published)

The Global Assistant should be DISABLED while an attempt is in progress.
Frontend checks: if examStore.active → hide the assistant button.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.championship import Championship
from app.models.user import User
from app.schemas.championship import (
    AnswerSave,
    EnterResponse,
    StudentResult,
    SubmitRequest,
    ViolationReport,
    ViolationResponse,
)
from app.services import championship_service

router = APIRouter(prefix="/championship", tags=["Weekly Championship"])


@router.get("")
async def list_championships(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lobby list: every non-draft championship visible to this student."""
    return {"championships": await championship_service.list_for_student(db, user)}


@router.get("/live")
async def live_championship(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return the currently live championship (if any) for the lobby screen."""
    row = (await db.execute(
        select(Championship).where(Championship.status == "live").limit(1)
    )).scalar_one_or_none()
    if not row:
        return {"live": False}
    paper = row.question_paper_json or []
    return {
        "live": True,
        "id": row.id,
        "title": row.title,
        "duration_secs": row.duration_secs,
        "question_count": len(paper) if isinstance(paper, list) else 0,
    }


@router.post("/{championship_id}/enter", response_model=EnterResponse)
async def enter_championship(
    championship_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await championship_service.enter(db, user, championship_id)


@router.put("/{championship_id}/answer")
async def save_answer(
    championship_id: str,
    payload: AnswerSave,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await championship_service.save_answer(db, user, championship_id, payload)


@router.post("/{championship_id}/submit", response_model=StudentResult)
async def submit_championship(
    championship_id: str,
    payload: SubmitRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await championship_service.submit(db, user, championship_id,
                                             payload.time_used_secs)


@router.post("/{championship_id}/violation", response_model=ViolationResponse)
async def report_violation(
    championship_id: str,
    payload: ViolationReport,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await championship_service.report_violation(db, user, championship_id)


@router.get("/{championship_id}/result", response_model=StudentResult)
async def championship_result(
    championship_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await championship_service.get_result(db, user, championship_id)
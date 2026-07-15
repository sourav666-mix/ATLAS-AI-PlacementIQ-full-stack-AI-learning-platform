# interview_studio.py - [NEW] start / turn / finish (voice interview loop)
# backend/app/routers/interview_studio.py
"""AI Interview Studio — endpoints.

  GET  /studio/domains              -> setup wizard catalog
  GET  /studio/sessions             -> my past sessions
  GET  /studio/sessions/{id}/report -> stored final report
  POST /studio/start                -> begin a session (ONE AI call: question set)
  POST /studio/{id}/turn            -> answer one question (ONE AI call per turn)
  POST /studio/{id}/finish          -> end + report (ONE AI call)

PRIVACY: this router accepts text and numbers only (enforced by the schemas).
Audio never reaches the backend — STT runs in the browser (Web Speech API),
TTS is returned as base64. Camera frames NEVER leave the device; the client's
useCameraPresence hook sends only a presence percentage.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.studio import (
    FinalReport,
    FinishRequest,
    SessionListItem,
    StartResponse,
    StudioSetup,
    TurnRequest,
    TurnResponse,
)
from app.services import studio_catalog, studio_service

router = APIRouter(prefix="/studio", tags=["AI Interview Studio"])


@router.get("/domains")
async def list_domains(_: User = Depends(get_current_user)):
    return {"domains": studio_catalog.list_domains(),
            "levels": studio_catalog.LEVELS,
            "question_counts": studio_catalog.QUESTION_COUNTS}


# declared before "/{session_id}/..." so "sessions" isn't captured as an id
@router.get("/sessions", response_model=list[SessionListItem])
async def my_sessions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await studio_service.list_sessions(db, user)


@router.get("/sessions/{session_id}/report", response_model=FinalReport)
async def session_report(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await studio_service.get_report(db, user, session_id)


@router.post("/start", response_model=StartResponse)
async def start_session(
    payload: StudioSetup,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await studio_service.start(db, user, payload)


@router.post("/{session_id}/turn", response_model=TurnResponse)
async def answer_turn(
    session_id: str,
    payload: TurnRequest,
    voice: bool = Query(True, description="return TTS audio for the reply"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await studio_service.turn(db, user, session_id, payload, voice_mode=voice)


@router.post("/{session_id}/finish", response_model=FinalReport)
async def finish_session(
    session_id: str,
    payload: FinishRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await studio_service.finish(db, user, session_id, payload.presence_pct)
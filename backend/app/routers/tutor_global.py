# tutor_global.py - [MOD] POST /tutor/global-chat (context-injected, voice optional)
# backend/app/routers/tutor_global.py
"""
Global AI Assistant routes (mounted at /tutor).

    POST /tutor/ask          -> personalized answer (assembles context, calls AI, logs turn)
    POST /tutor/global-chat  -> alias of /ask (the path the frontend panel calls;
                                extra fields like voice_mode are ignored)
    GET  /tutor/history      -> the student's recent assistant conversation
"""
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.tutor import TutorAskIn, TutorHistoryOut, TutorReplyOut
from app.services import tutor_service

from fastapi import HTTPException
from app.services.tutor_context_extras import assistant_disabled

router = APIRouter()


@router.post("/ask", response_model=TutorReplyOut)
@router.post("/global-chat", response_model=TutorReplyOut)
async def ask(
    payload: TutorAskIn,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if await assistant_disabled(db, current_user.id):
        raise HTTPException(status_code=423,
                            detail="Assistant is disabled during a live championship exam.")
    return await tutor_service.ask(db, current_user.id, payload.message, payload.source_page)


@router.get("/history", response_model=List[TutorHistoryOut])
async def history(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    return await tutor_service.get_history(db, current_user.id, limit)
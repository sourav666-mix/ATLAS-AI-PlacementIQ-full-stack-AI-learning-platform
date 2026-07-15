# backend/app/routers/skillpath_v12.py
"""
ATLAS AI 4.0 - v12 SkillPath Reforged: router.

Registered in main.py under /skillpath (additive snippet in
V12_BATCH1_SNIPPETS.md). Endpoint surface, mapped to the locked flow:

  GET  /skillpath/domains                                   Type A
  POST /skillpath/select                                    Type A
  GET  /skillpath/roadmap/{domain_id}                       Type A
  GET  /skillpath/topic/{topic_id}/learn                    Type A
  GET  /skillpath/topic/{topic_id}/subtopics                Type A
  GET  /skillpath/subtopic/{subtopic_id}/next-question      Type A*
  GET  /skillpath/subtopic/{subtopic_id}/progress           Type A
  POST /skillpath/subtopic/analyze                          Type B (1 AI call)

  * next-question is Type A from the pre-generated bank; it makes exactly
    one AI call ONLY when the student has exhausted all 25+ questions
    (generate-once-cache, saved back forever).
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.skillpath_v12 import (
    AnalyzeRequest,
    AnalysisResult,
    DomainListResponse,
    NextQuestionResponse,
    RoadmapResponse,
    SelectRequest,
    SelectResponse,
    SubtopicProgressResponse,
    SubtopicTabsResponse,
    TopicLearnResponse,
)
from app.services import (
    analysis_v12_service,
    learn_v12_service,
    practice_v12_service,
    skillpath_v12_service,
)

router = APIRouter(prefix="/skillpath", tags=["SkillPath v12"])


@router.get("/domains", response_model=DomainListResponse)
async def list_domains(db: AsyncSession = Depends(get_db)):
    """Step 1 - the nine locked domain cards. Type A."""
    return {"domains": await skillpath_v12_service.list_domains(db)}


@router.post("/select", response_model=SelectResponse)
async def select_domain_and_plan(
    payload: SelectRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Step 2 - domain FIRST, then plan (3/6/9). Type A, idempotent."""
    try:
        return await skillpath_v12_service.select_domain_and_plan(
            db, user.id, payload.domain_key, payload.plan_months
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/roadmap/{domain_id}", response_model=RoadmapResponse)
async def get_roadmap(
    domain_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Step 3 - roadmap cards with progress ring + status color. Type A."""
    try:
        return await skillpath_v12_service.get_roadmap(db, user.id, domain_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/topic/{topic_id}/learn", response_model=TopicLearnResponse)
async def get_topic_learn(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Step 4 - LEARN mode: what/when/how + 5 examples per subtopic + viz.
    Type A, seeded content only."""
    try:
        return await learn_v12_service.get_topic_learn(db, topic_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/topic/{topic_id}/subtopics", response_model=SubtopicTabsResponse)
async def get_subtopic_tabs(
    topic_id: str,
    domain_id: str = Query(..., description="active domain for progress"),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Steps 5-6 - Practice pressed: subtopic tabs with mastery ticks. Type A."""
    try:
        return await practice_v12_service.get_subtopic_tabs(
            db, user.id, topic_id, domain_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/subtopic/{subtopic_id}/next-question",
    response_model=NextQuestionResponse,
)
async def get_next_question(
    subtopic_id: str,
    domain_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Step 7 - next unseen question, difficulty order. Type A from the
    bank; generate-once-cache (1 AI call) only on exhaustion."""
    try:
        return await practice_v12_service.get_next_question(
            db, user.id, subtopic_id, domain_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/subtopic/{subtopic_id}/progress",
    response_model=SubtopicProgressResponse,
)
async def get_subtopic_progress(
    subtopic_id: str,
    domain_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Progress strip under the arena. Type A."""
    return await practice_v12_service.get_subtopic_progress(
        db, user.id, subtopic_id, domain_id
    )


@router.post("/subtopic/analyze", response_model=AnalysisResult)
async def analyze_attempt(
    payload: AnalyzeRequest,
    domain_id: str = Query(...),
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    """Step 8 - the ONE Type B endpoint: exactly one AI call, then pure
    deterministic mastery math + points."""
    try:
        return await analysis_v12_service.analyze_attempt(
            db,
            user_id=user.id,
            domain_id=domain_id,
            question_id=payload.question_id,
            answer_text=payload.answer_text,
            run_output=payload.run_output,
            time_taken_seconds=payload.time_taken_seconds,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

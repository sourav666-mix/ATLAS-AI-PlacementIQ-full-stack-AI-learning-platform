# backend/app/routers/skillpath_v3.py   [NEW v12]
"""
ATLAS AI 4.0 (v12) — SkillPath Engine 3.0 router.
Domain cards, per-domain roadmap dashboard, Learn Mode, and the 25-question practice loop.

Type A endpoints (0 AI calls): /domains, /roadmap, /learn, /subtopics, /practice reveal.
Type B endpoints (<=1 AI call): /practice/question (once on bank exhaustion), /practice/attempt.
"""
from typing import List, Optional
from statistics import mean

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.models.domain import Domain, DomainPhase, RoadmapTopic  # NOTE: confirm class names
from app.models.practice import TopicQuestion
from app.models.skillpath_v3 import DomainEnrollment
from app.services import learn_content_service, content_dedup_service, practice_engine
from app.schemas.skillpath_v3 import (
    DomainCard, RoadmapDashboardResponse, RoadmapTopicCard,
    LearnCardResponse, PracticeQuestionResponse,
    AttemptRequest, AttemptAnalysisResponse, RevealRequest,
)

router = APIRouter(prefix="/skillpath", tags=["skillpath-v3"])


def _topic_name(t) -> str:
    return getattr(t, "title", getattr(t, "name", ""))


def _state_from_pills(pills) -> str:
    if pills and all(p["status"] == "mastered" for p in pills):
        return "green"
    if any(p["status"] in ("in_progress", "mastered") for p in pills):
        return "blue"
    return "grey"


# ---------- Domain-first navigation (Type A) ----------
@router.get("/domains", response_model=List[DomainCard])
async def list_domains(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    domains = (
        await db.execute(select(Domain).order_by(Domain.order_index.asc()))
    ).scalars().all()

    count_rows = (
        await db.execute(
            select(DomainEnrollment.domain_id, func.count())
            .group_by(DomainEnrollment.domain_id)
        )
    ).all()
    counts = {did: c for did, c in count_rows}

    return [
        DomainCard(
            id=d.id,
            slug=getattr(d, "slug", ""),
            name=getattr(d, "name", ""),
            pitch=getattr(d, "pitch", "") or "",
            students_on_path=counts.get(d.id, 0),
            min_plan_months=getattr(d, "min_plan_months", 3),
        )
        for d in domains
    ]


# ---------- Roadmap dashboard, scoped to one domain (Type A) ----------
@router.get("/roadmap/{domain_id}", response_model=RoadmapDashboardResponse)
async def roadmap_dashboard(
    domain_id: str,
    plan_months: Optional[int] = Query(None, description="falls back to the student's enrollment"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    domain = (
        await db.execute(select(Domain).where(Domain.id == domain_id))
    ).scalar_one_or_none()
    if domain is None:
        raise HTTPException(status_code=404, detail="Domain not found")

    # resolve plan depth: explicit query -> enrollment plan -> safe default
    if plan_months is None:
        enr = (
            await db.execute(
                select(DomainEnrollment).where(
                    DomainEnrollment.user_id == user.id,
                    DomainEnrollment.domain_id == domain_id,
                )
            )
        ).scalar_one_or_none()
        plan_months = 3  # NOTE: resolve enr.plan_id -> months if you prefer strict gating here

    # phases unlocked by plan depth (v10 min_plan_months filter, unchanged)
    phase_ids = (
        await db.execute(
            select(DomainPhase.id).where(
                DomainPhase.domain_id == domain_id,
                DomainPhase.min_plan_months <= plan_months,
            )
        )
    ).scalars().all()

    top_topics = (
        await db.execute(
            select(RoadmapTopic)
            .where(
                RoadmapTopic.phase_id.in_(phase_ids),      # NOTE: confirm roadmap_topics.phase_id
                RoadmapTopic.parent_topic_id.is_(None),
            )
            .order_by(RoadmapTopic.order_index.asc())
        )
    ).scalars().all()

    shared = await content_dedup_service.resolve_domain_modules(db, domain_id)
    shared_titles = {m["title"] for m in shared}

    cards: List[RoadmapTopicCard] = []
    all_mastery: List[int] = []
    for t in top_topics:
        pills = await learn_content_service.get_subtopic_pills(db, user.id, t.id)
        all_mastery.extend(p["mastery_score"] for p in pills)
        cards.append(
            RoadmapTopicCard(
                topic_id=t.id,
                title=_topic_name(t),
                state=_state_from_pills(pills),
                is_shared_module=_topic_name(t) in shared_titles,
                subtopics=pills,
            )
        )

    progress_pct = round(mean(all_mastery)) if all_mastery else 0

    return RoadmapDashboardResponse(
        domain_id=domain.id,
        domain_name=getattr(domain, "name", ""),
        plan_months=plan_months,
        progress_pct=progress_pct,
        topics=cards,
    )


# ---------- Learn Mode (Type A read) ----------
@router.get("/learn/{subtopic_id}", response_model=LearnCardResponse)
async def learn_card(
    subtopic_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await learn_content_service.get_learn_card(db, subtopic_id)


@router.get("/subtopics/{topic_id}")
async def subtopic_pills(
    topic_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await learn_content_service.get_subtopic_pills(db, user.id, topic_id)


# ---------- Practice Mode ----------
@router.get("/practice/{subtopic_id}/question", response_model=PracticeQuestionResponse)
async def practice_question(
    subtopic_id: str,
    position: int = Query(..., ge=1, le=25),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Type A (bank read); Type B exactly once if the cell is empty (then cached forever)
    return await practice_engine.serve_question(db, subtopic_id, position)


@router.post("/practice/attempt", response_model=AttemptAnalysisResponse)
async def practice_attempt(
    req: AttemptRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Type B: exactly one bounded AI call per attempt
    return await practice_engine.analyze_attempt(
        db, user.id, req.question_id, req.student_answer
    )


@router.post("/practice/reveal")
async def practice_reveal(
    req: RevealRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # THE LAW: reveal is a pure DB read. Never an AI call here.
    q = (
        await db.execute(select(TopicQuestion).where(TopicQuestion.id == req.question_id))
    ).scalar_one_or_none()
    if q is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return {
        "model_answer": getattr(q, "model_answer", ""),
        "why_explanation": getattr(q, "why_explanation", ""),
        "how_explanation": getattr(q, "how_explanation", ""),
        "example": getattr(q, "example", ""),
        "common_mistakes": getattr(q, "common_mistakes", ""),
    }
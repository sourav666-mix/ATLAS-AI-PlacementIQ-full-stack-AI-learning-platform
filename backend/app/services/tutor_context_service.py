# tutor_context_service.py - [MOD] assemble_context(): + studio/championship/jobs signals
# backend/app/services/tutor_context_service.py
"""
Assembles the Global Assistant's context snapshot (System Understanding §11).

The assistant has NO memory. Before every message we build a fresh snapshot of
the student's real situation and inject it into the prompt. This module ONLY
reads student tables — it never writes.
"""
from typing import Optional

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_activity import DailyActivity
from app.models.domain import Domain, RoadmapTopic
from app.models.interview_studio import InterviewStudioSession
from app.models.job import JobTracking
from app.models.plan import UserSubscription
from app.models.practice import UserAttempt
from app.models.skill_progress import SkillRadarScore, UserTopicProgress
from app.models.user import User
from app.services import tutor_context_extras

async def assemble_context(db: AsyncSession, user_id: str) -> dict:
    user = await db.get(User, user_id)

    # domain (from active subscription)
    domain_name: Optional[str] = None
    sub = (
        await db.execute(
            select(UserSubscription)
            .where(UserSubscription.user_id == user_id, UserSubscription.status == "active")
            .order_by(desc(UserSubscription.started_at))
            .limit(1)
        )
    ).scalar_one_or_none()
    if sub is not None:
        domain = await db.get(Domain, sub.domain_id)
        domain_name = domain.name if domain else None

    # current topic
    current_topic = (
        await db.execute(
            select(RoadmapTopic.title)
            .join(UserTopicProgress, UserTopicProgress.topic_id == RoadmapTopic.id)
            .where(UserTopicProgress.user_id == user_id, UserTopicProgress.status == "current")
            .limit(1)
        )
    ).scalar_one_or_none()

    # weak areas = lowest-scoring radar categories
    weak_areas = list(
        (
            await db.execute(
                select(SkillRadarScore.skill_category)
                .where(SkillRadarScore.user_id == user_id)
                .order_by(SkillRadarScore.score.asc())
                .limit(3)
            )
        ).scalars().all()
    )

    # streak (latest daily row)
    streak = (
        await db.execute(
            select(DailyActivity.streak_days)
            .where(DailyActivity.user_id == user_id)
            .order_by(desc(DailyActivity.activity_date))
            .limit(1)
        )
    ).scalar() or 0

    # recent scores (last 5 attempts, chronological)
    recent = (
        await db.execute(
            select(UserAttempt.score)
            .where(UserAttempt.user_id == user_id, UserAttempt.score.isnot(None))
            .order_by(desc(UserAttempt.created_at))
            .limit(5)
        )
    ).scalars().all()
    recent_scores = list(reversed(list(recent)))

    # lightweight latest signals
    last_interview = (
        await db.execute(
            select(InterviewStudioSession.overall_score)
            .where(InterviewStudioSession.user_id == user_id)
            .order_by(desc(InterviewStudioSession.created_at))
            .limit(1)
        )
    ).scalar()
    jobs_saved = (
        await db.execute(
            select(func.count()).select_from(JobTracking).where(JobTracking.user_id == user_id)
        )
    ).scalar() or 0

    return {
        "domain": domain_name,
        "current_topic": current_topic,
        "weak_areas": weak_areas,
        "streak": int(streak),
        "recent_scores": recent_scores,
        "profile_bar_score": user.profile_bar_score if user else 0,
        "signals": {
            "last_interview_score": last_interview,
            "jobs_saved": int(jobs_saved),
        },
    }


__all__ = ["assemble_context"]
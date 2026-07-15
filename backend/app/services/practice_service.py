# practice_service.py - score_attempt() [live AI] ; reveal_answer() [DB only]
# backend/app/services/practice_service.py
"""
The core learning loop (System Understanding §3).

read concept -> attempt -> get scored -> see why it's right

COST RULES enforced here:
  * get_topic_content / list_questions / reveal_answer are PURE DB READS. No AI.
  * only score_attempt() calls live AI (via ai_provider_router).
  * only the FIRST attempt per question counts toward topic mastery.

Every scored attempt routes points through progress_engine (the scoring spine).
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.domain import RoadmapTopic
from app.models.practice import TopicContent, TopicQuestion, UserAttempt
from app.models.skill_progress import SkillRadarScore, UserTopicProgress
from app.services import ai_provider_router, progress_engine


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --- pure reads -------------------------------------------------------------
async def get_topic_content(db: AsyncSession, topic_id: str) -> Optional[TopicContent]:
    return (
        await db.execute(select(TopicContent).where(TopicContent.topic_id == topic_id))
    ).scalar_one_or_none()


async def list_questions(db: AsyncSession, topic_id: str) -> list[TopicQuestion]:
    return list(
        (
            await db.execute(
                select(TopicQuestion)
                .where(TopicQuestion.topic_id == topic_id)
                .order_by(TopicQuestion.order_index)
            )
        ).scalars().all()
    )


async def get_question(db: AsyncSession, question_id: str) -> Optional[TopicQuestion]:
    return await db.get(TopicQuestion, question_id)


async def reveal_answer(db: AsyncSession, question_id: str) -> dict:
    """Pure DB read of the stored explanation. NEVER calls AI."""
    q = await db.get(TopicQuestion, question_id)
    if q is None:
        raise ValueError("Question not found.")
    return {
        "question_id": q.id,
        "why_explanation": q.why_explanation,
        "how_explanation": q.how_explanation,
        "example": q.example,
        "common_mistakes": q.common_mistakes,
    }


# --- the one AI-backed action ----------------------------------------------
async def score_attempt(db: AsyncSession, user_id: str, question_id: str, student_answer: str) -> dict:
    q = await db.get(TopicQuestion, question_id)
    if q is None:
        raise ValueError("Question not found.")

    prior = (
        await db.execute(
            select(func.count()).select_from(UserAttempt).where(
                UserAttempt.user_id == user_id, UserAttempt.question_id == question_id
            )
        )
    ).scalar() or 0
    attempt_number = prior + 1
    is_first = attempt_number == 1

    result = await ai_provider_router.score_answer(q.question_text, q.model_answer, student_answer)
    score = int(result["score"])
    feedback = result["feedback"]

    db.add(UserAttempt(
        user_id=user_id,
        question_id=question_id,
        student_answer=student_answer,
        score=score,
        ai_feedback=feedback,
        attempt_number=attempt_number,
        is_first_attempt=is_first,
    ))
    await db.flush()

    # update topic mastery (first attempts only) + skill radar
    newly_completed, mastery = await _update_topic_progress(db, user_id, q.topic_id)

    # route points through the scoring spine (commits)
    await progress_engine.record_event(
        db, user_id, "question_attempted", {"score": score, "is_first_attempt": is_first}
    )
    if newly_completed:
        await progress_engine.record_event(db, user_id, "topic_completed", {})

    return {
        "score": score,
        "feedback": feedback,
        "attempt_number": attempt_number,
        "is_first_attempt": is_first,
        "mastery_score": mastery,
        "topic_completed": newly_completed,
    }


async def _update_topic_progress(db: AsyncSession, user_id: str, topic_id: str) -> tuple[bool, int]:
    """Recompute mastery from first-attempt scores; complete the topic if all done."""
    q_ids = list(
        (
            await db.execute(select(TopicQuestion.id).where(TopicQuestion.topic_id == topic_id))
        ).scalars().all()
    )
    total = len(q_ids)

    first_rows = (
        await db.execute(
            select(UserAttempt.question_id, UserAttempt.score).where(
                UserAttempt.user_id == user_id,
                UserAttempt.question_id.in_(q_ids),
                UserAttempt.is_first_attempt.is_(True),
            )
        )
    ).all()
    completed_qids = {qid for qid, _ in first_rows}
    scores = [sc for _, sc in first_rows if sc is not None]
    mastery = round(sum(scores) / len(scores) * 10) if scores else 0  # 0-10 -> 0-100

    utp = (
        await db.execute(
            select(UserTopicProgress).where(
                UserTopicProgress.user_id == user_id, UserTopicProgress.topic_id == topic_id
            )
        )
    ).scalar_one_or_none()
    if utp is None:
        utp = UserTopicProgress(user_id=user_id, topic_id=topic_id)
        db.add(utp)

    utp.questions_completed = len(completed_qids)
    utp.mastery_score = mastery
    newly_completed = False
    if utp.status != "completed":
        if total > 0 and len(completed_qids) >= total:
            utp.status = "completed"
            utp.completed_at = _now()
            newly_completed = True
        else:
            utp.status = "current"
            if utp.started_at is None:
                utp.started_at = _now()

    await db.flush()
    if newly_completed:
        await _advance_to_next_topic(db, user_id, utp)
    await _update_radar(db, user_id, topic_id)
    return newly_completed, mastery


async def _advance_to_next_topic(db: AsyncSession, user_id: str, completed: UserTopicProgress) -> None:
    """When a topic completes, promote the next 'not_started' topic to 'current'."""
    from app.models.domain import DomainPhase  # local import to avoid cycles

    already_current = (
        await db.execute(
            select(func.count()).select_from(UserTopicProgress).where(
                UserTopicProgress.user_id == user_id,
                UserTopicProgress.subscription_id == completed.subscription_id,
                UserTopicProgress.status == "current",
            )
        )
    ).scalar() or 0
    if already_current:
        return  # something is already current; don't jump ahead

    nxt = (
        await db.execute(
            select(UserTopicProgress)
            .join(RoadmapTopic, UserTopicProgress.topic_id == RoadmapTopic.id)
            .join(DomainPhase, RoadmapTopic.phase_id == DomainPhase.id)
            .where(
                UserTopicProgress.user_id == user_id,
                UserTopicProgress.subscription_id == completed.subscription_id,
                UserTopicProgress.status == "not_started",
            )
            .order_by(DomainPhase.order_index, RoadmapTopic.order_index)
            .limit(1)
        )
    ).scalar_one_or_none()
    if nxt is not None:
        nxt.status = "current"
        nxt.started_at = _now()
        await db.flush()
# backend/app/services/analysis_v12_service.py
"""
ATLAS AI 4.0 - v12 SkillPath Reforged: AI ANALYSIS (spec Section 2 step 8
+ Section 6 'analysis prompt discipline').

Type B - EXACTLY ONE live AI call per submission. Genuinely per-student,
cannot be cached. Groq primary, Gemini/Cerebras/SambaNova fallback - all
routed through the one gateway:

    from app.services.ai_provider_router import complete as ask_ai, parse_json

Analysis prompt discipline (locked):
  the analyzer receives the question, the model solution, and the
  student's attempt; it returns ONLY JSON:
    {score, verdict, good, missing, walkthrough, next_hint}
  Lenient on style, strict on concept - same rule as v9/v10.

Everything AFTER the AI call is pure deterministic math:
  * score clamped 0-100, verdict normalized
  * correct at score >= 60; mastery at >= 20/25 correct
  * points via the locked pure formula (progress_engine spine)
"""

import json
import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.practice import TopicQuestion, UserAttempt
from app.services.ai_provider_router import complete as ask_ai, parse_json
from app.services.curriculum_registry import CORRECT_SCORE_THRESHOLD
from app.services.practice_v12_service import record_attempt_progress
from app.prompts import ANALYZE_ATTEMPT_SYSTEM, ANALYZE_ATTEMPT_USER

logger = logging.getLogger(__name__)

# Pure points formula (deterministic; progress_engine remains the single
# scoring spine - it consumes points_awarded via the daily activity hook).
_POINTS_BASE = {"basic": 10, "medium": 20, "advanced": 35}
_MASTERY_BONUS = 50
_TOPIC_COMPLETE_BONUS = 100


def compute_points(difficulty: str, score: int,
                   subtopic_mastered: bool, topic_complete: bool,
                   counted: bool) -> int:
    """Pure math, zero AI. Repeat attempts on a seen question earn 0."""
    if not counted or score < CORRECT_SCORE_THRESHOLD:
        return 0
    pts = round(_POINTS_BASE.get(difficulty, 10) * (score / 100))
    if subtopic_mastered:
        pts += _MASTERY_BONUS
    if topic_complete:
        pts += _TOPIC_COMPLETE_BONUS
    return pts


def _normalize_verdict(raw: str, score: int) -> str:
    v = str(raw or "").strip().lower().replace(" ", "_")
    if v in ("correct", "partially_correct", "incorrect"):
        return v
    # deterministic fallback from the score band
    if score >= 85:
        return "correct"
    if score >= CORRECT_SCORE_THRESHOLD:
        return "partially_correct"
    return "incorrect"


def _clamp_score(raw) -> int:
    try:
        return max(0, min(100, int(round(float(raw)))))
    except (TypeError, ValueError):
        return 0


async def analyze_attempt(
    db: AsyncSession,
    user_id: str,
    domain_id: str,
    question_id: str,
    answer_text: str,
    run_output: Optional[str] = None,
    time_taken_seconds: Optional[int] = None,
) -> dict:
    question = (
        await db.execute(
            select(TopicQuestion).where(TopicQuestion.id == question_id)
        )
    ).scalars().first()
    if question is None:
        raise ValueError("Question not found")

    body = (question.body_json if isinstance(question.body_json, dict)
            else json.loads(question.body_json or "{}"))
    model_solution = body.get("model_solution", "")
    why_how = body.get("why_how", "")

    # ------------------------------------------------------------------
    # THE one AI call (Type B). Everything else in this function is math.
    # ------------------------------------------------------------------
    raw = await ask_ai(
        ANALYZE_ATTEMPT_SYSTEM,
        ANALYZE_ATTEMPT_USER.format(
            question=body.get("question", ""),
            question_kind=question.question_kind or "text",
            model_solution=model_solution,
            student_attempt=answer_text[:20_000],
            run_output=(run_output or "not provided")[:8_000],
        ),
    )
    try:
        parsed = parse_json(raw)
    except Exception:                                    # noqa: BLE001
        logger.warning("analysis parse failed for question %s", question_id)
        parsed = {}

    score = _clamp_score(parsed.get("score"))
    verdict = _normalize_verdict(parsed.get("verdict"), score)
    good = [str(g)[:300] for g in (parsed.get("good") or [])[:5]]
    missing = [str(m)[:300] for m in (parsed.get("missing") or [])[:5]]
    walkthrough = str(parsed.get("walkthrough", "")) or why_how
    next_hint = str(parsed.get("next_hint", ""))[:500]

    # deterministic progress transition (per-student-per-domain)
    prog = await record_attempt_progress(
        db, user_id=user_id, subtopic_id=question.topic_id,
        domain_id=domain_id, question_id=question_id, score=score,
    )
    points = compute_points(
        question.difficulty or "basic", score,
        prog["subtopic_mastered"], prog["topic_complete"], prog["counted"],
    )

    attempt = UserAttempt(
        user_id=user_id,
        question_id=question_id,
        student_answer=answer_text[:20_000],
        score=score,
        ai_feedback=json.dumps({
            "_verdict": verdict, "_good": good, "_missing": missing,
            "_next_hint": next_hint,
            "_time_taken_seconds": time_taken_seconds,
            "_domain_id": domain_id,
            "_points": points,
        }),
    )
    db.add(attempt)
    await db.commit()

    return {
        "question_id": question_id,
        "score": score,
        "verdict": verdict,
        "good": good,
        "missing": missing,
        "walkthrough": walkthrough[:6_000],
        "model_solution": str(model_solution)[:6_000],
        "next_hint": next_hint,
        "subtopic_mastered": prog["subtopic_mastered"],
        "topic_complete": prog["topic_complete"],
        "points_awarded": points,
    }

# FILE: backend/app/services/practice_engine.py   [v12 — FIXED]
"""
ATLAS AI 4.0 (v12) — the 25-question AI-adaptive practice loop.

Difficulty split: 1-10 basic, 11-20 medium, 21-25 advanced.

Cost rules:
  serve_question   -> Type A (bank read). Type B EXACTLY ONCE on bank exhaustion,
                      then cached forever.
  analyze_attempt  -> Type B, EXACTLY ONE bounded AI call per attempt.
  mastery / points -> pure deterministic math, routed through progress_engine
                      (the ONE scoring spine). No AI ever decides points.

COLUMN SHIM: v10's TopicQuestion / UserAttempt column names are resolved at import
so this file works whether the FK is `topic_id` or `subtopic_id`, whether the text
column is `statement` or `question_text`, etc. No schema change required.
"""
from typing import Dict, Any, List

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.ai_provider_router import complete as ask_ai, parse_json
from app.services import progress_engine
from app.models.practice import TopicQuestion, UserAttempt
from app.models.skillpath_v3 import SubtopicProgress

TOTAL_QUESTIONS = 25


# ---------------------------------------------------------------- column shim
def _attr(model, *candidates: str) -> str:
    """Return the first attribute name that actually exists on the model."""
    for name in candidates:
        if hasattr(model, name):
            return name
    raise AttributeError(
        f"{model.__name__} has none of: {candidates}. Fix the candidate list."
    )


# TopicQuestion columns
Q_FK = _attr(TopicQuestion, "subtopic_id", "topic_id")            # link to roadmap_topics
Q_TEXT = _attr(TopicQuestion, "statement", "question_text", "text")
Q_ANSWER = _attr(TopicQuestion, "model_answer", "answer", "solution")

# UserAttempt columns
A_QID = _attr(UserAttempt, "question_id", "topic_question_id")
A_TEXT = _attr(UserAttempt, "answer", "student_answer", "answer_text", "submitted_answer")


def _has(model, name: str) -> bool:
    return hasattr(model, name)


def _kwargs(model, data: Dict[str, Any]) -> Dict[str, Any]:
    """Drop any key the model doesn't actually have — prevents TypeError on insert."""
    return {k: v for k, v in data.items() if _has(model, k)}


# ------------------------------------------------- pure-math helpers (zero AI)
def tier_for_position(position: int) -> str:
    if position <= 10:
        return "basic"
    if position <= 20:
        return "medium"
    return "advanced"


def review_depth_for_position(position: int) -> str:
    if position <= 10:
        return "Give a short verdict, what's good, what's missing, and one hint. No follow-up."
    if position <= 20:
        return (
            "Give the verdict, what's good, what's missing, one hint, "
            "and a brief complexity / edge-case note."
        )
    return (
        "Give interview-grade feedback: verdict, what's good, what's missing, one hint, "
        "and one follow-up question a senior engineer would ask next."
    )


def recompute_mastery(questions_completed: int) -> int:
    return round(min(questions_completed, TOTAL_QUESTIONS) / TOTAL_QUESTIONS * 100)


def _examples(q) -> List[Dict[str, str]]:
    raw = getattr(q, "examples_json", None) or []
    out = []
    for item in raw[:2]:
        if isinstance(item, dict):
            out.append(
                {
                    "prompt": str(item.get("prompt", item.get("input", ""))),
                    "solution": str(item.get("solution", item.get("output", ""))),
                }
            )
    return out


def _serialize_question(q, position: int) -> Dict[str, Any]:
    return {
        "question_id": q.id,
        "subtopic_id": getattr(q, Q_FK, None),
        "position": position,
        "of_total": TOTAL_QUESTIONS,
        "difficulty_tier": getattr(q, "difficulty_tier", None) or tier_for_position(position),
        "question_kind": getattr(q, "question_kind", None)
        or getattr(q, "question_type", None)
        or "text",
        "statement": getattr(q, Q_TEXT, "") or "",
        "constraints": getattr(q, "constraints", None),
        "examples": _examples(q),
        "source": "auto" if getattr(q, "review_status", "") == "auto" else "seed",
    }


# ------------------------------- serve: bank-first, generate-once-cache-forever
async def serve_question(db: AsyncSession, subtopic_id: str, position: int) -> Dict[str, Any]:
    if position < 1 or position > TOTAL_QUESTIONS:
        raise HTTPException(status_code=400, detail="position must be 1..25")

    q = (
        await db.execute(
            select(TopicQuestion).where(
                getattr(TopicQuestion, Q_FK) == subtopic_id,
                TopicQuestion.position_index == position,
            )
        )
    ).scalars().first()

    if q is not None:
        return _serialize_question(q, position)   # Type A — pure bank read

    q = await _generate_and_cache(db, subtopic_id, position)   # Type B — once
    return _serialize_question(q, position)


async def _generate_and_cache(db: AsyncSession, subtopic_id: str, position: int):
    tier = tier_for_position(position)
    system = (
        "You author practice questions for ATLAS AI, a placement-prep platform for "
        "Indian B.Tech students. Return STRICT JSON only, no prose, no code fences."
    )
    prompt = (
        f"Create ONE {tier}-difficulty practice question for subtopic id {subtopic_id}. "
        "Include EXACTLY 2 worked examples. Return JSON with keys: "
        '{"statement": str, "constraints": str, "question_kind": "text|code|math|sql", '
        '"model_answer": str, "why_explanation": str, "how_explanation": str, '
        '"example": str, "common_mistakes": str, '
        '"examples": [{"prompt": str, "solution": str}, {"prompt": str, "solution": str}]}'
    )
    raw = await ask_ai(system, prompt)
    d = parse_json(raw) or {}

    data = {
        Q_FK: subtopic_id,
        "position_index": position,
        "difficulty_tier": tier,
        Q_TEXT: d.get("statement", ""),
        Q_ANSWER: d.get("model_answer", ""),
        "constraints": d.get("constraints", ""),
        "examples_json": (d.get("examples") or [])[:2],
        "question_kind": d.get("question_kind", "text"),
        "question_type": d.get("question_kind", "text"),
        "why_explanation": d.get("why_explanation", ""),
        "how_explanation": d.get("how_explanation", ""),
        "example": d.get("example", ""),
        "common_mistakes": d.get("common_mistakes", ""),
        "review_status": "auto",
    }
    q = TopicQuestion(**_kwargs(TopicQuestion, data))
    db.add(q)
    await db.commit()
    await db.refresh(q)
    return q


# --------------------------- analyze: exactly ONE bounded AI call per attempt
async def analyze_attempt(
    db: AsyncSession, user_id: str, question_id: str, student_answer: str
) -> Dict[str, Any]:
    q = (
        await db.execute(select(TopicQuestion).where(TopicQuestion.id == question_id))
    ).scalars().first()
    if q is None:
        raise HTTPException(status_code=404, detail="Question not found")

    position = getattr(q, "position_index", 1) or 1
    subtopic_id = getattr(q, Q_FK, "")

    system = (
        "You are a strict but fair examiner for ATLAS AI. Review the student's attempt "
        "against the model answer. NEVER reveal the full answer. Return STRICT JSON only."
    )
    prompt = (
        f"{review_depth_for_position(position)}\n\n"
        f"QUESTION: {getattr(q, Q_TEXT, '')}\n"
        f"MODEL ANSWER: {getattr(q, Q_ANSWER, '')}\n"
        f"STUDENT ANSWER: {student_answer}\n\n"
        'Return JSON: {"verdict": str, "whats_good": str, "whats_missing": str, '
        '"hint": str, "followup": str, "score": int(0-10)}'
    )
    raw = await ask_ai(system, prompt)
    a = parse_json(raw) or {}
    score = int(a.get("score", 0) or 0)

    is_first = await _is_first_attempt(db, user_id, question_id)

    # persist the attempt row
    attempt_data = {
        "user_id": user_id,
        A_QID: question_id,
        A_TEXT: student_answer,
        "score": score,
        "is_correct": score >= 6,
        "feedback": a.get("verdict", ""),
    }
    db.add(UserAttempt(**_kwargs(UserAttempt, attempt_data)))

    # deterministic mastery — first attempt only
    prog = await _get_or_create_progress(db, user_id, subtopic_id)
    mastered_now = False
    if is_first and prog.questions_completed < TOTAL_QUESTIONS:
        prog.questions_completed += 1
        prog.mastery_score = recompute_mastery(prog.questions_completed)
        prog.status = "in_progress"
        if prog.questions_completed >= TOTAL_QUESTIONS:
            prog.status = "mastered"
            mastered_now = True

    await db.commit()

    # points via the ONE scoring spine (it commits internally)
    if is_first:
        await progress_engine.record_event(
            db, user_id, "question_attempted",
            {"score": score, "is_first_attempt": True},
        )
    if mastered_now:
        await progress_engine.record_event(db, user_id, "topic_completed", {})

    return {
        "verdict": a.get("verdict", ""),
        "whats_good": a.get("whats_good", ""),
        "whats_missing": a.get("whats_missing", ""),
        "hint": a.get("hint", ""),
        "followup": a.get("followup") if position >= 21 else None,
        "score": score,
        "counter": prog.questions_completed,
        "subtopic_status": prog.status,
        "can_advance": True,
    }


# --------------------------------------------- internal helpers (zero AI)
async def _is_first_attempt(db: AsyncSession, user_id: str, question_id: str) -> bool:
    count = (
        await db.execute(
            select(func.count()).select_from(UserAttempt).where(
                UserAttempt.user_id == user_id,
                getattr(UserAttempt, A_QID) == question_id,
            )
        )
    ).scalar_one()
    return count == 0


async def _get_or_create_progress(
    db: AsyncSession, user_id: str, subtopic_id: str
) -> SubtopicProgress:
    prog = (
        await db.execute(
            select(SubtopicProgress).where(
                SubtopicProgress.user_id == user_id,
                SubtopicProgress.subtopic_id == subtopic_id,
            )
        )
    ).scalars().first()
    if prog is None:
        prog = SubtopicProgress(
            user_id=user_id,
            subtopic_id=subtopic_id,
            questions_completed=0,
            mastery_score=0,
            status="in_progress",
        )
        db.add(prog)
        await db.flush()
    return prog
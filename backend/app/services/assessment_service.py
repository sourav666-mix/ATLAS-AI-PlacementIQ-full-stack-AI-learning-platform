# assessment_service.py - [MOD] merged interview+aptitude eval + lifetime analytics
# backend/app/services/assessment_service.py
"""
Assessment Center: Aptitude Pro + Mock Interview Pro (Type-B surfaces).

Aptitude MCQs are SCORED BY PURE MATH (compare selected vs correct index) — no
AI needed for scoring, only optional generation. Mock answers are open-ended and
AI-EVALUATED (with a local fallback). Both feed the profile bar's
assessment_history component, so completion triggers a profile-bar recompute.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import AptitudeSession, MockSession
from app.services import ai_provider_router, prompts, progress_engine, question_bank


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================================
# generation (AI-first, bank fallback)
# ============================================================================
async def _generate_aptitude(category: str, level: str, count: int) -> list[dict]:
    try:
        text = await ai_provider_router.complete(
            prompts.aptitude_gen_system(), prompts.aptitude_gen_user(category, level, count)
        )
        data = ai_provider_router.parse_json(text)
        out = []
        for q in data.get("questions", [])[:count]:
            opts = list(q.get("options", []))[:4]
            if len(opts) != 4:
                continue
            out.append({
                "question": str(q["question"]),
                "options": [str(o) for o in opts],
                "correct_index": int(q["correct_index"]),
                "explanation": str(q.get("explanation", "")),
            })
        if out:
            return out
    except Exception:
        pass
    return question_bank.aptitude(category, count)


async def _generate_mock(role: str, domain: str, level: str, count: int) -> list[str]:
    try:
        text = await ai_provider_router.complete(
            prompts.mock_gen_system(), prompts.mock_gen_user(role, domain, level, count)
        )
        data = ai_provider_router.parse_json(text)
        qs = [str(q) for q in data.get("questions", [])][:count]
        if qs:
            return qs
    except Exception:
        pass
    return question_bank.mock(domain, count)


# ============================================================================
# Aptitude Pro
# ============================================================================
async def start_aptitude(db: AsyncSession, user_id: str, category: str, level: str, count: int) -> dict:
    questions = await _generate_aptitude(category, level, count)
    session = AptitudeSession(
        user_id=user_id,
        category=category,
        level=level,
        total_questions=len(questions),
        questions_json=questions,          # includes correct_index (server-side only)
        status="in_progress",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    public = [{"index": i, "question": q["question"], "options": q["options"]}
              for i, q in enumerate(questions)]
    return {"session_id": session.id, "category": category, "level": level, "questions": public}


async def submit_aptitude(db: AsyncSession, user_id: str, session_id: str, answers: list[int]) -> dict:
    session = await db.get(AptitudeSession, session_id)
    if session is None or session.user_id != user_id:
        raise ValueError("Aptitude session not found.")
    if session.status == "completed":
        raise ValueError("This session was already submitted.")

    questions = session.questions_json or []
    breakdown = []
    correct = 0
    for i, q in enumerate(questions):
        selected = answers[i] if i < len(answers) else -1
        is_correct = selected == q["correct_index"]
        correct += int(is_correct)
        breakdown.append({
            "index": i,
            "selected": selected,
            "correct_index": q["correct_index"],
            "is_correct": is_correct,
            "explanation": q.get("explanation", ""),
        })

    total = len(questions)
    score = round(correct / total * 100) if total else 0

    session.answers_json = answers
    session.correct_count = correct
    session.score = score
    session.accuracy = (correct / total) if total else 0.0
    session.status = "completed"
    session.completed_at = _now()
    await db.flush()

    await progress_engine.recompute_profile_bar(db, user_id)
    await db.commit()

    return {"session_id": session_id, "score": score, "correct_count": correct,
            "total": total, "accuracy": session.accuracy, "breakdown": breakdown}


# ============================================================================
# Mock Interview Pro
# ============================================================================
async def start_mock(db: AsyncSession, user_id: str, role: str, domain: Optional[str], level: str, count: int) -> dict:
    questions = await _generate_mock(role, domain or "", level, count)
    session = MockSession(
        user_id=user_id,
        role=role,
        domain=domain,
        level=level,
        questions_json=[{"question": q} for q in questions],
        status="in_progress",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    public = [{"index": i, "question": q} for i, q in enumerate(questions)]
    return {"session_id": session.id, "role": role, "questions": public}


def _local_eval(question: str, answer: str) -> dict:
    n = len((answer or "").split())
    if n == 0:
        return {"score": 0, "feedback": "No answer provided."}
    if n >= 40:
        return {"score": 7, "feedback": "Good depth. Add a concrete example to strengthen it."}
    if n >= 15:
        return {"score": 5, "feedback": "On the right track — expand with specifics and structure (STAR)."}
    return {"score": 3, "feedback": "Too brief. Explain your reasoning and give an example."}


async def _evaluate_answer(question: str, answer: str) -> dict:
    try:
        text = await ai_provider_router.complete(
            prompts.mock_eval_system(), prompts.mock_eval_user(question, answer)
        )
        data = ai_provider_router.parse_json(text)
        score = int(max(0, min(10, int(data["score"]))))
        feedback = str(data.get("feedback") or "").strip() or "Evaluated."
        return {"score": score, "feedback": feedback}
    except Exception:
        return _local_eval(question, answer)


async def submit_mock(db: AsyncSession, user_id: str, session_id: str, answers: list[str]) -> dict:
    session = await db.get(MockSession, session_id)
    if session is None or session.user_id != user_id:
        raise ValueError("Mock session not found.")
    if session.status == "completed":
        raise ValueError("This session was already submitted.")

    questions = [q["question"] for q in (session.questions_json or [])]
    breakdown = []
    total_score = 0
    for i, question in enumerate(questions):
        answer = answers[i] if i < len(answers) else ""
        result = await _evaluate_answer(question, answer)
        total_score += result["score"]
        breakdown.append({"index": i, "question": question,
                          "score": result["score"], "feedback": result["feedback"]})

    overall = round((total_score / (len(questions) * 10)) * 100) if questions else 0
    summary = (f"You averaged {overall}/100 across {len(questions)} questions. "
               "Focus on structure and concrete examples to level up.")

    session.answers_json = answers
    session.per_question_json = breakdown
    session.overall_score = overall
    session.feedback = summary
    session.status = "completed"
    session.completed_at = _now()
    await db.flush()

    await progress_engine.recompute_profile_bar(db, user_id)
    await db.commit()

    return {"session_id": session_id, "overall_score": overall,
            "breakdown": breakdown, "summary": summary}


# ============================================================================
# history (both types, merged)
# ============================================================================
async def get_history(db: AsyncSession, user_id: str, limit: int = 20) -> list[dict]:
    apt = (
        await db.execute(
            select(AptitudeSession).where(
                AptitudeSession.user_id == user_id, AptitudeSession.status == "completed"
            ).order_by(desc(AptitudeSession.completed_at)).limit(limit)
        )
    ).scalars().all()
    mock = (
        await db.execute(
            select(MockSession).where(
                MockSession.user_id == user_id, MockSession.status == "completed"
            ).order_by(desc(MockSession.completed_at)).limit(limit)
        )
    ).scalars().all()

    items = [
        {"id": a.id, "kind": "aptitude", "label": a.category, "score": a.score,
         "completed_at": a.completed_at}
        for a in apt
    ] + [
        {"id": m.id, "kind": "mock", "label": m.role, "score": m.overall_score,
         "completed_at": m.completed_at}
        for m in mock
    ]
    items.sort(key=lambda x: x["completed_at"] or _now(), reverse=True)
    return items[:limit]


# ============================================================================
# analytics (lifetime, aptitude + mock)
# ============================================================================
async def get_analytics(db: AsyncSession, user_id: str) -> dict:
    apt = (
        await db.execute(
            select(AptitudeSession).where(
                AptitudeSession.user_id == user_id, AptitudeSession.status == "completed"
            ).order_by(AptitudeSession.completed_at)
        )
    ).scalars().all()
    mock_count = (
        await db.execute(
            select(MockSession).where(
                MockSession.user_id == user_id, MockSession.status == "completed"
            )
        )
    ).scalars().all()

    aptitude_solved = sum(a.correct_count for a in apt)
    accuracies = [a.accuracy for a in apt if a.accuracy is not None]
    avg_accuracy = round(sum(accuracies) / len(accuracies) * 100, 1) if accuracies else 0.0

    accuracy_trend = [
        {"label": a.completed_at.strftime("%b %d") if a.completed_at else f"#{i + 1}",
         "value": round((a.accuracy or 0) * 100)}
        for i, a in enumerate(apt[-10:])
    ]

    by_category: dict[str, list[float]] = {}
    for a in apt:
        by_category.setdefault(a.category or "General", []).append(a.accuracy or 0)
    weakest_subtopics = sorted(
        ({"name": cat, "accuracy": round(sum(vals) / len(vals) * 100, 1)}
         for cat, vals in by_category.items()),
        key=lambda x: x["accuracy"],
    )[:5]

    return {
        "aptitude_solved": aptitude_solved,
        "mock_sessions": len(mock_count),
        "avg_accuracy": avg_accuracy,
        "accuracy_trend": accuracy_trend,
        "weakest_subtopics": weakest_subtopics,
    }


__all__ = [
    "start_aptitude", "submit_aptitude",
    "start_mock", "submit_mock",
    "get_history", "get_analytics",
]
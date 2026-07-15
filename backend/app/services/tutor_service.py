# backend/app/services/tutor_service.py
"""
Global AI Assistant orchestration.

ask() = assemble fresh context -> build personalized prompt -> call the AI
gateway -> log the turn to tutor_history. The assistant has NO memory; the ONLY
table it writes to is tutor_history (its own chat log).

If no AI provider is configured, we return a friendly context-aware fallback so
the endpoint still works offline (and tests stay deterministic).
"""
from typing import Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tutor_history import TutorHistory
from app.services import ai_provider_router, prompts, tutor_context_service


def _fallback_reply(message: str, context: dict) -> str:
    topic = context.get("current_topic")
    streak = context.get("streak", 0)
    bits = []
    if topic:
        bits.append(f"You're currently on **{topic}**")
    if streak:
        bits.append(f"and you're on a {streak}-day streak — keep it going")
    lead = (", ".join(bits) + ". ") if bits else ""
    return (
        f"{lead}I can't reach the live tutor right now (no AI provider is "
        "configured), but here's a tip: re-read the concept card for your current "
        "topic, then attempt the question again and use 'reveal' to compare. "
        f"You asked: \"{message.strip()[:160]}\"."
    )


async def ask(db: AsyncSession, user_id: str, message: str, source_page: Optional[str] = None) -> dict:
    context = await tutor_context_service.assemble_context(db, user_id)
    system = prompts.tutor_system(context)

    try:
        answer = await ai_provider_router.complete(system, message)
    except ai_provider_router.ProviderUnavailable:
        answer = _fallback_reply(message, context)

    row = TutorHistory(
        user_id=user_id,
        message=message,
        response=answer,
        context_snapshot=context,
        source_page=source_page,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)

    return {"response": answer, "context_used": context}


async def get_history(db: AsyncSession, user_id: str, limit: int = 20) -> list[TutorHistory]:
    rows = (
        await db.execute(
            select(TutorHistory)
            .where(TutorHistory.user_id == user_id)
            .order_by(desc(TutorHistory.created_at))
            .limit(limit)
        )
    ).scalars().all()
    return list(rows)


__all__ = ["ask", "get_history"]
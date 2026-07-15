# FILE: backend/app/scripts/seed_practice_questions.py   [v12 — FIXED]
"""
ATLAS AI 4.0 (v12) — author the 25-question bank per subtopic (10 basic / 10 medium / 5 advanced).

*** ALL questions AND answers are AI-generated here — ONCE, offline. ***
Read forever at zero per-student cost. Crash-resumable (commits per question).
Uses the same column shim as practice_engine, so it adapts to your real schema.

Run:  python -m app.scripts.seed_practice_questions
      python -m app.scripts.seed_practice_questions --domain data_science
"""
import asyncio
import sys

from sqlalchemy import select, func

from app.database import AsyncSessionLocal
from app.services.ai_provider_router import complete as ask_ai, parse_json
from app.services.practice_engine import Q_FK, Q_TEXT, Q_ANSWER, _kwargs, tier_for_position
from app.models.domain import RoadmapTopic
from app.models.practice import TopicQuestion
from app.prompts import PRACTICE_QUESTION_SYSTEM, PRACTICE_QUESTION_PROMPT

TOTAL = 25


async def _count_existing(db, subtopic_id: str) -> int:
    return (
        await db.execute(
            select(func.count()).select_from(TopicQuestion).where(
                getattr(TopicQuestion, Q_FK) == subtopic_id
            )
        )
    ).scalar_one()


async def _seed_subtopic(db, subtopic: RoadmapTopic, domain_name: str) -> int:
    subtopic_id = subtopic.id
    have = await _count_existing(db, subtopic_id)
    if have >= TOTAL:
        return 0  # already complete — resumable skip

    name = getattr(subtopic, "title", "")
    made = 0
    for position in range(have + 1, TOTAL + 1):
        tier = tier_for_position(position)
        prompt = PRACTICE_QUESTION_PROMPT.format(
            tier=tier, subtopic=name, domain=domain_name, position=position
        )
        try:
            raw = await ask_ai(PRACTICE_QUESTION_SYSTEM, prompt)
            d = parse_json(raw) or {}
        except Exception as e:
            print(f"[err] {name} Q{position}: {e}")
            continue

        if not d.get("statement"):
            print(f"[warn] {name} Q{position}: empty statement, skipping")
            continue

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
            "review_status": "published",
        }
        db.add(TopicQuestion(**_kwargs(TopicQuestion, data)))
        await db.commit()   # per-question commit -> crash-resumable
        made += 1
        print(f"[ok] {name} Q{position}/{TOTAL} ({tier})")
    return made


async def main(only_domain: str | None = None):
    async with AsyncSessionLocal() as db:
        subtopics = (
            await db.execute(
                select(RoadmapTopic).where(RoadmapTopic.parent_topic_id.isnot(None))
            )
        ).scalars().all()

        print(f"found {len(subtopics)} subtopics")
        total_made = 0
        for st in subtopics:
            try:
                total_made += await _seed_subtopic(db, st, only_domain or "")
            except Exception as e:
                print(f"[err] {getattr(st, 'title', '?')}: {e}")
        print(f"seed_practice_questions: {total_made} questions authored")


if __name__ == "__main__":
    dom = sys.argv[sys.argv.index("--domain") + 1] if "--domain" in sys.argv else None
    asyncio.run(main(dom))
# backend/app/scripts/seed_domain_learn_cards.py   [NEW v12]
"""
ATLAS AI 4.0 (v12) — author Learn Cards for every subtopic across all 9 domains.

AI-authored Type-A content, generated ONCE and written to roadmap_topics
(what_is_it / when_to_use / how_to_use / examples_json[5] / visualization_config_json).
Resumable: skips any subtopic that already has what_is_it filled.
Providers rotate automatically inside ask_ai (Groq -> Gemini -> Cerebras -> SambaNova).

Run:  python -m app.scripts.seed_domain_learn_cards
Seed order (Data Science first as the reference): pass --domain data_science to limit.
"""
import asyncio
import sys

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.services.ai_provider_router import complete as ask_ai, parse_json
from app.models.domain import RoadmapTopic
from app.prompts import LEARN_CARD_SYSTEM, LEARN_CARD_PROMPT


async def _seed_one(db, subtopic: RoadmapTopic, parent_name: str, domain_name: str) -> bool:
    if getattr(subtopic, "what_is_it", None):
        return False  # already seeded — resumable skip

    name = getattr(subtopic, "title", getattr(subtopic, "name", ""))
    prompt = LEARN_CARD_PROMPT.format(subtopic=name, topic=parent_name, domain=domain_name)
    raw = await ask_ai(LEARN_CARD_SYSTEM, prompt)
    data = parse_json(raw) or {}

    subtopic.what_is_it = data.get("what_is_it", "")
    subtopic.when_to_use = data.get("when_to_use", "")
    subtopic.how_to_use = data.get("how_to_use", "")
    subtopic.examples_json = (data.get("examples") or [])[:5]
    subtopic.visualization_config_json = data.get("visualization_config") or {"type": "table", "params": []}
    await db.flush()
    return True


async def main(only_domain: str | None = None):
    async with AsyncSessionLocal() as db:
        # every subtopic = a roadmap_topics row with a parent
        subtopics = (
            await db.execute(
                select(RoadmapTopic).where(RoadmapTopic.parent_topic_id.isnot(None))
            )
        ).scalars().all()

        # cache parent names for context
        parents = {
            t.id: getattr(t, "title", getattr(t, "name", ""))
            for t in (await db.execute(select(RoadmapTopic))).scalars().all()
        }

        seeded = 0
        for st in subtopics:
            parent_name = parents.get(getattr(st, "parent_topic_id", None), "")
            domain_name = only_domain or ""    # NOTE: resolve real domain via phase->domain if you want it in the prompt
            try:
                if await _seed_one(db, st, parent_name, domain_name):
                    seeded += 1
                    await db.commit()
                    print(f"[ok] learn card: {parent_name} / {getattr(st,'title','')}")
            except Exception as e:  # keep going; re-run resumes where it stopped
                print(f"[err] {getattr(st,'title','?')}: {e}")
        print(f"seed_domain_learn_cards: {seeded} new cards")


if __name__ == "__main__":
    dom = sys.argv[sys.argv.index("--domain") + 1] if "--domain" in sys.argv else None
    asyncio.run(main(dom))
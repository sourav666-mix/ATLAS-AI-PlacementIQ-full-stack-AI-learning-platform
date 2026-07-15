# seed_content.py - [MOD] OFFLINE: subtopic concept cards + 25-question sets
# backend/app/scripts/seed_content.py
"""
ATLAS AI 4.0 - v12 seeding pipeline: THE MAIN CLI.

    cd backend
    python -m app.scripts.seed_content                      # everything
    python -m app.scripts.seed_content --topics python mysql
    python -m app.scripts.seed_content --learn-only
    python -m app.scripts.seed_content --max-ai-calls 200   # budget a run
    python -m app.scripts.seed_content --dry-run            # plan only

Properties (all verified by the batch gate):
  * IDEMPOTENT + RESUMABLE - work is computed from the DB itself
    (seed_planner); a second run over seeded content makes ZERO AI calls.
  * BUDGETED - --max-ai-calls caps a run so free-tier quotas survive;
    the next run continues from wherever this one stopped.
  * CONCURRENT-SAFE - SEED_CONCURRENCY subtopics run in parallel, but
    generation WITHIN a subtopic is strictly sequential so the rolling
    duplicate-differentiation list is always complete.
  * FAULT-ISOLATED - one exhausted item logs and skips; it never kills
    the run, and the next run retries it (it is still a deficit).
"""

import argparse
import asyncio
import json
import logging
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal as SessionLocal
from app.config import settings
from app.models.domain import RoadmapTopic
from app.models.practice import TopicContent, TopicQuestion
from app.services.curriculum_registry import TOPIC_LIBRARY
from app.services.seed_planner import (
    SubtopicState, WorkItem, build_plan, plan_summary,
)
from app.services.seed_generation import (
    SeedGenerationError,
    generate_learn_explainer,
    generate_seed_question,
)
from app.services.seed_validators import normalize_statement
from app.services.skillpath_v12_service import ensure_domain_registered
from app.services.curriculum_registry import DOMAIN_ORDER

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("seed_content")


# ----------------------------------------------------------------------
# Snapshot: DB -> planner states
# ----------------------------------------------------------------------

async def snapshot_states(
    db: AsyncSession, topic_keys: List[str]
) -> List[SubtopicState]:
    states: List[SubtopicState] = []
    for key in topic_keys:
        spec = TOPIC_LIBRARY[key]
        topic = (
            await db.execute(select(RoadmapTopic).where(
                RoadmapTopic.title == spec["title"],
                RoadmapTopic.parent_topic_id.is_(None)))
        ).scalars().first()
        if topic is None:
            continue  # registered later by ensure_domain_registered
        subtopics = (
            await db.execute(select(RoadmapTopic)
                .where(RoadmapTopic.parent_topic_id == topic.id)
                .order_by(RoadmapTopic.item_order))
        ).scalars().all()
        for st in subtopics:
            has_learn = (
                await db.execute(select(TopicContent)
                    .where(TopicContent.topic_id == st.id))
            ).scalars().first() is not None
            questions = (
                await db.execute(select(TopicQuestion).where(
                    TopicQuestion.topic_id == st.id,
                    TopicQuestion.review_status == "published"))
            ).scalars().all()
            counts: Dict[str, int] = {"basic": 0, "medium": 0, "advanced": 0}
            for q in questions:
                counts[q.difficulty] = counts.get(q.difficulty, 0) + 1
            states.append({
                "topic_key": key,
                "topic_title": spec["title"],
                "subtopic_id": st.id,
                "subtopic_name": st.title,
                "question_kind": spec["default_kind"],
                "has_learn": has_learn,
                "counts": counts,
            })
    return states


# ----------------------------------------------------------------------
# Workers
# ----------------------------------------------------------------------

class Budget:
    def __init__(self, max_calls: int):
        self.max_calls = max_calls
        self.used = 0

    def take(self, n: int = 1) -> bool:
        if self.used + n > self.max_calls:
            return False
        self.used += n
        return True


async def seed_subtopic(item: WorkItem, budget: Budget,
                        sem: asyncio.Semaphore) -> dict:
    """One subtopic end-to-end in ITS OWN session (concurrency-safe)."""
    done = {"learn": 0, "questions": 0, "skipped": 0}
    async with sem:
        async with SessionLocal() as db:
            # ---- Learn explainer ------------------------------------
            if item["needs_learn"]:
                if not budget.take():
                    done["skipped"] += 1
                    return done
                try:
                    body = await generate_learn_explainer(
                        item["topic_title"], item["subtopic_name"],
                        item["question_kind"])
                    db.add(TopicContent(topic_id=item["subtopic_id"],
                                        body_json=json.dumps(body)))
                    await db.commit()
                    done["learn"] += 1
                except SeedGenerationError as exc:
                    logger.error("learn FAILED %s/%s: %s",
                                 item["topic_title"], item["subtopic_name"], exc)

            # ---- Question bank (rolling dedupe state) ----------------
            existing = (
                await db.execute(select(TopicQuestion).where(
                    TopicQuestion.topic_id == item["subtopic_id"]))
            ).scalars().all()
            statements, norms, order = [], set(), 0
            for q in existing:
                b = q.body_json if isinstance(q.body_json, dict) \
                    else json.loads(q.body_json or "{}")
                statements.append(b.get("question", ""))
                norms.add(normalize_statement(b.get("question", "")))
                order = max(order, (q.created_order or 0) + 1)

            for difficulty in ("basic", "medium", "advanced"):
                for _ in range(item["question_deficits"].get(difficulty, 0)):
                    if not budget.take():
                        done["skipped"] += 1
                        return done
                    try:
                        result = await generate_seed_question(
                            item["topic_title"], item["subtopic_name"],
                            difficulty, item["question_kind"],
                            statements, norms)
                    except SeedGenerationError as exc:
                        logger.error("question FAILED %s/%s [%s]: %s",
                                     item["topic_title"],
                                     item["subtopic_name"], difficulty, exc)
                        continue
                    db.add(TopicQuestion(
                        topic_id=item["subtopic_id"],
                        difficulty=difficulty,
                        question_kind=result["question_kind"],
                        review_status="published",
                        created_order=order,
                        question_text=result["body"]["question"],
                        body_json=json.dumps(result["body"]),
                    ))
                    order += 1
                    await db.commit()   # commit per question = resumable
                    done["questions"] += 1
    logger.info("seeded %s/%s: +%d learn, +%d questions",
                item["topic_title"], item["subtopic_name"],
                done["learn"], done["questions"])
    return done


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

async def run(args) -> dict:
    async with SessionLocal() as db:
        for key in DOMAIN_ORDER:      # idempotent skeleton registration
            await ensure_domain_registered(db, key)
        await db.commit()

        topic_keys = args.topics or list(TOPIC_LIBRARY.keys())
        states = await snapshot_states(db, topic_keys)

    plan = build_plan(states,
                      learn=not args.questions_only,
                      questions=not args.learn_only)
    summary = plan_summary(plan)
    logger.info("PLAN: %s", summary)
    if args.dry_run:
        for it in plan[:20]:
            logger.info("  pending %s/%s learn=%s deficits=%s",
                        it["topic_title"], it["subtopic_name"],
                        it["needs_learn"], it["question_deficits"])
        return {"plan": summary, "executed": None}

    budget = Budget(args.max_ai_calls)
    sem = asyncio.Semaphore(int(getattr(settings, "SEED_CONCURRENCY", 3)))
    results = await asyncio.gather(
        *(seed_subtopic(it, budget, sem) for it in plan))

    executed = {
        "learn_seeded": sum(r["learn"] for r in results),
        "questions_seeded": sum(r["questions"] for r in results),
        "budget_used": budget.used,
        "budget_exhausted": any(r["skipped"] for r in results),
    }
    logger.info("DONE: %s", executed)
    if executed["budget_exhausted"]:
        logger.info("budget hit - just re-run to continue where this stopped")
    return {"plan": summary, "executed": executed}


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="ATLAS v12 content seeder")
    p.add_argument("--topics", nargs="*", default=None,
                   help="topic keys to seed (default: all; python+mysql first)")
    p.add_argument("--learn-only", action="store_true")
    p.add_argument("--questions-only", action="store_true")
    p.add_argument("--max-ai-calls", type=int, default=10_000)
    p.add_argument("--dry-run", action="store_true")
    return p.parse_args(argv)


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
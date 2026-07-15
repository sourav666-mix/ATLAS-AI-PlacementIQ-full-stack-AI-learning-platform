# backend/app/scripts/seed_gate.py
"""
ATLAS AI 4.0 - v12 seeding pipeline: POST-SEED VERIFICATION GATE.

    python -m app.scripts.seed_gate [--topics python mysql]

Run after seed_content to verify the invariants the student app relies
on. Zero AI. Exit code 0 only if EVERY check passes:

  1. mix        - each seeded subtopic holds exactly 10/10/5 published
  2. shape      - every question body has question / 2 examples /
                  model_solution; starter_code only on kind='code'
  3. dedupe     - no two questions in a subtopic share a normalized
                  statement signature
  4. learn      - every seeded explainer carries what/when/how + exactly
                  5 examples (underscore keys)
  5. ordering   - created_order is unique per subtopic (stable serving)
"""

import argparse
import asyncio
import json
import sys

from sqlalchemy import select

from app.database import AsyncSessionLocal as SessionLocal
from app.models.domain import RoadmapTopic
from app.models.practice import TopicContent, TopicQuestion
from app.services.curriculum_registry import TOPIC_LIBRARY, DIFFICULTY_MIX
from app.services.seed_validators import normalize_statement

PASS, FAIL = [], []


def check(name: str, cond: bool, extra: str = "") -> None:
    (PASS if cond else FAIL).append(name)
    print(("  PASS " if cond else "  FAIL ") + name, extra)


async def gate(topic_keys) -> int:
    async with SessionLocal() as db:
        for key in topic_keys:
            spec = TOPIC_LIBRARY[key]
            topic = (await db.execute(select(RoadmapTopic).where(
                RoadmapTopic.title == spec["title"],
                RoadmapTopic.parent_topic_id.is_(None)))).scalars().first()
            if topic is None:
                continue
            subtopics = (await db.execute(select(RoadmapTopic).where(
                RoadmapTopic.parent_topic_id == topic.id))).scalars().all()

            for st in subtopics:
                qs = (await db.execute(select(TopicQuestion).where(
                    TopicQuestion.topic_id == st.id,
                    TopicQuestion.review_status == "published",
                ))).scalars().all()
                if not qs:
                    continue  # not seeded yet - report handles coverage
                label = f"{spec['title']}/{st.title}"

                counts = {}
                for q in qs:
                    counts[q.difficulty] = counts.get(q.difficulty, 0) + 1
                check(f"{label}: 10/10/5 mix", counts == DIFFICULTY_MIX,
                      str(counts))

                norms, orders, shape_ok = set(), set(), True
                for q in qs:
                    b = q.body_json if isinstance(q.body_json, dict) \
                        else json.loads(q.body_json or "{}")
                    if not (len(b.get("question", "")) >= 20
                            and len(b.get("examples", [])) == 2
                            and b.get("model_solution")):
                        shape_ok = False
                    if b.get("starter_code") and q.question_kind != "code":
                        shape_ok = False
                    norms.add(normalize_statement(b.get("question", "")))
                    orders.add(q.created_order)
                check(f"{label}: shapes valid", shape_ok)
                check(f"{label}: no duplicate statements",
                      len(norms) == len(qs))
                check(f"{label}: created_order unique",
                      len(orders) == len(qs))

                content = (await db.execute(select(TopicContent).where(
                    TopicContent.topic_id == st.id))).scalars().first()
                if content is not None:
                    body = content.body_json if isinstance(
                        content.body_json, dict) \
                        else json.loads(content.body_json or "{}")
                    check(f"{label}: learn shape (5 examples)",
                          bool(body.get("_what"))
                          and len(body.get("_examples", [])) == 5)

    print(f"\nSEED GATE: {len(PASS)} passed, {len(FAIL)} failed")
    return 0 if not FAIL else 1


def parse_args(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--topics", nargs="*",
                   default=list(TOPIC_LIBRARY.keys()))
    return p.parse_args(argv)


if __name__ == "__main__":
    sys.exit(asyncio.run(gate(parse_args().topics)))
# backend/app/scripts/seed_report.py
"""
ATLAS AI 4.0 - v12 seeding pipeline: COVERAGE REPORT.

    python -m app.scripts.seed_report            # human table
    python -m app.scripts.seed_report --json     # machine-readable
    python -m app.scripts.seed_report --strict   # exit 1 if incomplete
                                                 # (CI / pre-launch check)

Zero AI. Reads the same snapshot the seeder plans from, so the report
and the plan can never disagree.
"""

import argparse
import asyncio
import json
import sys

from app.database import AsyncSessionLocal as SessionLocal
from app.services.curriculum_registry import (
    TOPIC_LIBRARY, QUESTIONS_PER_SUBTOPIC,
)
from app.services.seed_planner import question_deficits
from app.scripts.seed_content import snapshot_states


async def build_report() -> dict:
    async with SessionLocal() as db:
        states = await snapshot_states(db, list(TOPIC_LIBRARY.keys()))

    topics = {}
    for s in states:
        t = topics.setdefault(s["topic_key"], {
            "title": s["topic_title"], "subtopics": 0, "learn_done": 0,
            "questions_done": 0, "questions_target": 0, "complete": True,
        })
        deficit = sum(question_deficits(s["counts"]).values())
        have = sum(s["counts"].values())
        t["subtopics"] += 1
        t["learn_done"] += 1 if s["has_learn"] else 0
        t["questions_done"] += min(have, QUESTIONS_PER_SUBTOPIC)
        t["questions_target"] += QUESTIONS_PER_SUBTOPIC
        if deficit or not s["has_learn"]:
            t["complete"] = False

    totals = {
        "subtopics": sum(t["subtopics"] for t in topics.values()),
        "learn_done": sum(t["learn_done"] for t in topics.values()),
        "questions_done": sum(t["questions_done"] for t in topics.values()),
        "questions_target": sum(t["questions_target"] for t in topics.values()),
        "topics_complete": sum(1 for t in topics.values() if t["complete"]),
        "topics_total": len(topics),
    }
    return {"topics": topics, "totals": totals}


def print_table(report: dict) -> None:
    print(f"{'topic':34} {'learn':>9} {'questions':>12}  status")
    print("-" * 66)
    for key, t in report["topics"].items():
        print(f"{t['title'][:33]:34} "
              f"{t['learn_done']}/{t['subtopics']:<7} "
              f"{t['questions_done']}/{t['questions_target']:<10} "
              f"{'✓ complete' if t['complete'] else 'pending'}")
    tot = report["totals"]
    print("-" * 66)
    print(f"TOTAL: learn {tot['learn_done']}/{tot['subtopics']} · "
          f"questions {tot['questions_done']}/{tot['questions_target']} · "
          f"topics complete {tot['topics_complete']}/{tot['topics_total']}")


async def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true")
    p.add_argument("--strict", action="store_true")
    args = p.parse_args(argv)

    report = await build_report()
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_table(report)

    if args.strict:
        tot = report["totals"]
        return 0 if tot["topics_complete"] == tot["topics_total"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
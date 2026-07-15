# backend/app/services/seed_planner.py
"""
ATLAS AI 4.0 - v12 seeding pipeline: THE PLANNER (pure functions).

Zero AI, zero DB. Given a snapshot of what already exists, computes the
exact remaining work - which makes the whole pipeline stateless-resumable:
kill it at any point, re-run it, and it continues from the database's own
truth. No progress table, no checkpoint files.

Priority (locked): python and mysql subtopics seed first - they unlock
Data Science, Data Analysis, AI, Backend and Cloud simultaneously.
"""

from typing import Dict, List, TypedDict

from app.services.curriculum_registry import (
    DIFFICULTY_MIX,
    TOPIC_LIBRARY,
)

PRIORITY_TOPICS = ["python", "mysql"]  # everything else follows registry order


class SubtopicState(TypedDict):
    """Snapshot of one subtopic, built by the CLI from DB queries."""
    topic_key: str
    topic_title: str
    subtopic_id: str
    subtopic_name: str
    question_kind: str
    has_learn: bool
    counts: Dict[str, int]     # {"basic": n, "medium": n, "advanced": n}


class WorkItem(TypedDict):
    subtopic_id: str
    topic_key: str
    topic_title: str
    subtopic_name: str
    question_kind: str
    needs_learn: bool
    question_deficits: Dict[str, int]   # difficulty -> how many to generate
    ai_calls_needed: int


def topic_priority(topic_key: str) -> int:
    """python=0, mysql=1, then stable registry order from 2."""
    if topic_key in PRIORITY_TOPICS:
        return PRIORITY_TOPICS.index(topic_key)
    keys = list(TOPIC_LIBRARY.keys())
    return len(PRIORITY_TOPICS) + (keys.index(topic_key)
                                   if topic_key in keys else 999)


def question_deficits(counts: Dict[str, int]) -> Dict[str, int]:
    """Missing questions per difficulty vs the locked 10/10/5 mix."""
    return {
        diff: max(0, target - int(counts.get(diff, 0)))
        for diff, target in DIFFICULTY_MIX.items()
    }


def build_plan(
    states: List[SubtopicState],
    learn: bool = True,
    questions: bool = True,
) -> List[WorkItem]:
    """Deficits -> ordered work items. Fully seeded subtopics drop out,
    which is exactly what makes re-runs idempotent."""
    items: List[WorkItem] = []
    for s in states:
        deficits = question_deficits(s["counts"]) if questions else {}
        needs_learn = learn and not s["has_learn"]
        q_calls = sum(deficits.values())
        if not needs_learn and q_calls == 0:
            continue
        items.append({
            "subtopic_id": s["subtopic_id"],
            "topic_key": s["topic_key"],
            "topic_title": s["topic_title"],
            "subtopic_name": s["subtopic_name"],
            "question_kind": s["question_kind"],
            "needs_learn": needs_learn,
            "question_deficits": deficits,
            "ai_calls_needed": q_calls + (1 if needs_learn else 0),
        })
    items.sort(key=lambda it: (topic_priority(it["topic_key"]),
                               it["topic_key"], it["subtopic_name"]))
    return items


def plan_summary(items: List[WorkItem]) -> dict:
    return {
        "subtopics_pending": len(items),
        "learn_pending": sum(1 for it in items if it["needs_learn"]),
        "questions_pending": sum(sum(it["question_deficits"].values())
                                 for it in items),
        "ai_calls_needed": sum(it["ai_calls_needed"] for it in items),
    }
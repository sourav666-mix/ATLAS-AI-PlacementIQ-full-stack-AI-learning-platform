# backend/app/scripts/seed_championship.py
"""Seed a demo championship (status=draft) with a curated 20-question paper.

    py -3.11 -m app.scripts.seed_championship
    py -3.11 -m app.scripts.seed_championship --created-by <admin_users.id>
    py -3.11 -m app.scripts.seed_championship --live   # fast-track to live for testing

Idempotent: skips if a championship with the same title exists.
"""
from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.championship import Championship

TITLE = "ATLAS AI Weekly Challenge — Demo"

PAPER = [
    {"index": 0, "text": "What is the time complexity of binary search?",
     "kind": "mcq", "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"], "correct": "O(log n)", "points": 5},
    {"index": 1, "text": "Which data structure uses LIFO?",
     "kind": "mcq", "options": ["Queue", "Stack", "Heap", "Graph"], "correct": "Stack", "points": 5},
    {"index": 2, "text": "15 × 15 = ?",
     "kind": "rapid", "options": ["200", "225", "250", "215"], "correct": "225", "points": 5},
    {"index": 3, "text": "What does SQL JOIN do?",
     "kind": "mcq", "options": ["Deletes rows", "Combines rows from tables",
     "Creates indexes", "Sorts data"], "correct": "Combines rows from tables", "points": 5},
    {"index": 4, "text": "Which sort is O(n log n) average AND worst case?",
     "kind": "mcq", "options": ["QuickSort", "MergeSort", "BubbleSort", "SelectionSort"],
     "correct": "MergeSort", "points": 5},
    {"index": 5, "text": "If a train travels 300 km in 5 hours, what is the speed in m/s?",
     "kind": "math", "options": ["15.67", "16.67", "17.67", "18.67"],
     "correct": "16.67", "points": 5},
    {"index": 6, "text": "What is the output of: print(type([]) is list)?",
     "kind": "mcq", "options": ["True", "False", "Error", "None"], "correct": "True", "points": 5},
    {"index": 7, "text": "In OOP, which principle hides internal details?",
     "kind": "mcq", "options": ["Inheritance", "Polymorphism", "Encapsulation", "Abstraction"],
     "correct": "Encapsulation", "points": 5},
    {"index": 8, "text": "Which is NOT a valid HTTP method?",
     "kind": "mcq", "options": ["GET", "POST", "SAVE", "DELETE"], "correct": "SAVE", "points": 5},
    {"index": 9, "text": "A circle has area 154 cm². Approx radius?",
     "kind": "math", "options": ["5 cm", "7 cm", "9 cm", "11 cm"], "correct": "7 cm", "points": 5},
    {"index": 10, "text": "Which layer of OSI handles routing?",
     "kind": "mcq", "options": ["Transport", "Network", "Data Link", "Application"],
     "correct": "Network", "points": 5},
    {"index": 11, "text": "Complete: A, C, F, J, ?",
     "kind": "logic", "options": ["N", "O", "P", "Q"], "correct": "O", "points": 5},
    {"index": 12, "text": "What does ACID stand for in databases?",
     "kind": "mcq", "options": [
         "Atomicity, Consistency, Isolation, Durability",
         "Access, Control, Integrity, Data",
         "Add, Create, Insert, Delete",
         "Automatic, Concurrent, Indexed, Distributed"],
     "correct": "Atomicity, Consistency, Isolation, Durability", "points": 5},
    {"index": 13, "text": "If P(A) = 0.3 and P(B) = 0.5 (independent), what is P(A∩B)?",
     "kind": "math", "options": ["0.15", "0.8", "0.2", "0.35"], "correct": "0.15", "points": 5},
    {"index": 14, "text": "Dijkstra's algorithm fails with:",
     "kind": "mcq", "options": ["Directed graphs", "Negative weights", "Sparse graphs", "Cycles"],
     "correct": "Negative weights", "points": 5},
    {"index": 15, "text": "In Python, what is `{'a':1} | {'b':2}`?",
     "kind": "mcq", "options": ["Error", "{'a':1,'b':2}", "{'ab':3}", "None"],
     "correct": "{'a':1,'b':2}", "points": 5},
    {"index": 16, "text": "How many edges in a complete graph K₅?",
     "kind": "math", "options": ["5", "10", "15", "20"], "correct": "10", "points": 5},
    {"index": 17, "text": "Which design pattern ensures only one instance?",
     "kind": "mcq", "options": ["Factory", "Observer", "Singleton", "Strategy"],
     "correct": "Singleton", "points": 5},
    {"index": 18, "text": "If 8 workers finish a job in 12 days, how many days for 6 workers?",
     "kind": "math", "options": ["14", "16", "18", "20"], "correct": "16", "points": 5},
    {"index": 19, "text": "REST API status 201 means:",
     "kind": "mcq", "options": ["OK", "Created", "Not Found", "Unauthorized"],
     "correct": "Created", "points": 5},
]


async def _resolve_admin(db, override):
    if override:
        return override
    try:
        from app.models.admin_user import AdminUser
        row = (await db.execute(select(AdminUser).limit(1))).scalars().first()
        return getattr(row, "id", None) if row else None
    except Exception:
        return None


async def seed(created_by, go_live: bool) -> None:
    async with AsyncSessionLocal() as db:
        admin_id = await _resolve_admin(db, created_by)
        if not admin_id:
            print("  No admin_users row. Pass --created-by <id> or create a super_admin first.")
            return
        existing = (await db.execute(
            select(Championship).where(Championship.title == TITLE)
        )).scalar_one_or_none()
        if existing:
            print(f"  skip  '{TITLE}' already exists (status={existing.status})")
            if go_live and existing.status == "draft":
                existing.status = "live"
                await db.commit()
                print(f"  -> fast-tracked to live")
            return
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        status = "live" if go_live else "draft"
        db.add(Championship(
            id=str(uuid.uuid4()),
            title=TITLE,
            college_id=None,
            starts_at=now + timedelta(minutes=5),
            duration_secs=900,
            question_paper_json=PAPER,
            status=status,
            created_by=admin_id,
        ))
        await db.commit()
        print(f"  ok  '{TITLE}' created ({status}, 20 questions)")


def main() -> None:
    created_by = None
    if "--created-by" in sys.argv:
        i = sys.argv.index("--created-by")
        if i + 1 < len(sys.argv):
            created_by = sys.argv[i + 1]
    go_live = "--live" in sys.argv
    print("Seeding demo championship...")
    asyncio.run(seed(created_by, go_live))
    print("Done.")


if __name__ == "__main__":
    main()
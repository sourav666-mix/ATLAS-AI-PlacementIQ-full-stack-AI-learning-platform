# backend/app/services/championship_paper_builder.py
"""AI-assisted paper draft for the Championship PaperBuilder UI.

Admin writes some questions manually and optionally asks the AI to generate
the rest. This is a DRAFT assist — the admin always reviews and edits before
scheduling the championship (the paper is editable while status = 'draft').

Cost: one AI call per draft request, which happens at most a few times per
event. This is well within the spec's cost model.
"""
from __future__ import annotations

import json

from app.schemas.championship import PaperQuestion
from app.services.ai_provider_router import complete as ask_ai, parse_json


async def generate_draft_questions(
    count: int = 20,
    existing: list[PaperQuestion] | None = None,
    difficulty: str = "medium-to-advanced",
) -> list[PaperQuestion]:
    """Generate `count` championship-style questions via AI.

    If `existing` questions are provided, the AI fills the remaining slots and
    avoids duplication.
    """
    already = len(existing or [])
    need = max(0, count - already)
    if need == 0:
        return existing or []

    existing_texts = [q.text for q in (existing or [])]
    existing_summary = "\n".join(f"- {t}" for t in existing_texts[:10])

    system = (
        "You are a B.Tech placement exam question writer. Generate championship-"
        "style questions: MCQs, rapid quiz, math tricks, and logic mini-games. "
        "Difficulty: medium to advanced. Respond with STRICT JSON only."
    )
    message = (
        f"Generate exactly {need} questions for a 15-minute proctored championship.\n"
        f"Mix: ~60% MCQ, ~20% rapid/math, ~20% logic.\n"
        f"Difficulty: {difficulty}.\n\n"
    )
    if existing_summary:
        message += f"Already in the paper (avoid overlap):\n{existing_summary}\n\n"
    message += (
        "Return a JSON array of objects, each with:\n"
        '{"index": N, "text": "...", "kind": "mcq|rapid|math|logic", '
        '"options": ["A","B","C","D"], "correct": "B", "points": 5}\n'
        f"Start index at {already}. Output JSON array only."
    )

    try:
        raw = await ask_ai(system, message)
        data = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(data, dict):
            data = data.get("questions") or data.get("items") or []
        if not isinstance(data, list):
            data = []
    except Exception:
        data = [{"index": already + i, "text": f"[Draft Q{already + i + 1}]",
                 "kind": "mcq", "options": ["A", "B", "C", "D"],
                 "correct": "A", "points": 5}
                for i in range(need)]

    generated: list[PaperQuestion] = []
    for i, item in enumerate(data[:need]):
        if not isinstance(item, dict):
            continue
        generated.append(PaperQuestion(
            index=already + i,
            text=item.get("text", f"[Q{already + i + 1}]"),
            kind=item.get("kind", "mcq"),
            options=item.get("options", []),
            correct=item.get("correct", ""),
            points=int(item.get("points", 5)),
        ))

    return list(existing or []) + generated
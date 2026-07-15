# backend/app/services/seed_validators.py
"""
ATLAS AI 4.0 - v12 seeding pipeline: SHAPE GUARDS (pure functions).

Every byte an LLM produces passes through here before touching MySQL.
Deterministic clamps + a normalized-statement duplicate check - the
platform never trusts model output blindly, even offline.
"""

import re
from typing import Iterable, List, Set

MAX_QUESTION_CHARS = 4_000
MAX_SOLUTION_CHARS = 6_000
LEARN_EXAMPLES = 5

_WS_RE = re.compile(r"\s+")


class SeedValidationError(ValueError):
    """Raised when generated content fails shape validation -> retry."""


def normalize_statement(text: str) -> str:
    """Case/whitespace/punct-insensitive signature for dedupe."""
    return _WS_RE.sub(" ", re.sub(r"[^\w\s]", "", str(text).lower())).strip()


def is_duplicate(statement: str, existing_norms: Set[str]) -> bool:
    return normalize_statement(statement) in existing_norms


def _two_examples(raw) -> List[dict]:
    examples = list(raw or [])[:2]
    if len(examples) < 2:
        raise SeedValidationError("question needs exactly 2 examples")
    return [{
        "input": str(e.get("input", ""))[:500],
        "output": str(e.get("output", ""))[:500],
        "why": str(e.get("why", ""))[:400],
    } for e in examples]


def validate_question_body(parsed: dict, question_kind_hint: str) -> dict:
    """LLM JSON -> the locked Section-6 body shape, or raise."""
    if not isinstance(parsed, dict):
        raise SeedValidationError("question payload is not an object")
    question = str(parsed.get("question", "")).strip()
    if len(question) < 20:
        raise SeedValidationError("question text too short")
    solution = str(parsed.get("model_solution", "")).strip()
    if len(solution) < 10:
        raise SeedValidationError("model_solution missing")

    kind = parsed.get("question_kind")
    if kind not in ("code", "text", "sql", "math"):
        kind = question_kind_hint

    starter = str(parsed.get("starter_code") or "").strip()
    return {
        "body": {
            "question": question[:MAX_QUESTION_CHARS],
            "examples": _two_examples(parsed.get("examples")),
            "starter_code": starter[:2_000] if (starter and kind == "code") else None,
            "model_solution": solution[:MAX_SOLUTION_CHARS],
            "why_how": str(parsed.get("why_how", ""))[:3_000],
            "common_mistakes": [str(m)[:300]
                                for m in (parsed.get("common_mistakes") or [])[:5]],
        },
        "question_kind": kind,
    }


def validate_learn_body(parsed: dict) -> dict:
    """LLM JSON -> the locked Learn explainer shape (underscore keys)."""
    if not isinstance(parsed, dict):
        raise SeedValidationError("learn payload is not an object")
    what = str(parsed.get("what_it_is", "")).strip()
    if len(what) < 30:
        raise SeedValidationError("what_it_is too short")

    examples = list(parsed.get("examples") or [])
    if len(examples) < LEARN_EXAMPLES:
        raise SeedValidationError(
            f"learn explainer needs {LEARN_EXAMPLES} examples, got {len(examples)}")
    cleaned = [{
        "title": str(e.get("title", f"Example {i + 1}"))[:150],
        "code": str(e.get("code", ""))[:2_500],
        "output": str(e.get("output", ""))[:1_500],
        "why": str(e.get("why", ""))[:600],
    } for i, e in enumerate(examples[:LEARN_EXAMPLES])]

    return {
        "_what": what[:3_000],
        "_when": str(parsed.get("when_to_use", ""))[:2_000],
        "_how": str(parsed.get("how_to_use", ""))[:2_500],
        "_examples": cleaned,
    }


def statements_for_prompt(statements: Iterable[str],
                          max_items: int = 30, max_chars: int = 140) -> str:
    """The differentiation block: the most recent statements, truncated,
    numbered - fed back to the model with an explicit 'must differ' rule."""
    tail = list(statements)[-max_items:]
    if not tail:
        return "none yet - this is the first question in this set."
    return "\n".join(f"{i + 1}. {s[:max_chars]}" for i, s in enumerate(tail))
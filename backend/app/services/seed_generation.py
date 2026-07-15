# backend/app/services/seed_generation.py
"""
ATLAS AI 4.0 - v12 seeding pipeline: BOUNDED GENERATION.

The ONLY file in the pipeline that calls AI, and only through the locked
gateway alias. Every call is wrapped in validate-or-retry:

    generate -> parse_json -> shape guard -> dedupe check
       |                                        |
       +---- SeedValidationError? retry with an explicit correction
             nudge (max SEED_MAX_RETRIES, exponential backoff between
             attempts to be gentle to the free-tier providers)

The duplicate-differentiation rule (hard-won in the v11 sessions): the
question prompt always carries the list of statements already generated
for this subtopic plus an explicit "must test something different"
instruction - without it, models converge on the same 3-4 questions.
"""

import asyncio
import logging
from typing import List, Set

from app.services.ai_provider_router import complete as ask_ai, parse_json
from app.services.seed_validators import (
    SeedValidationError,
    is_duplicate,
    normalize_statement,
    statements_for_prompt,
    validate_learn_body,
    validate_question_body,
)
from app.prompts import (
    SEED_LEARN_SYSTEM,
    SEED_LEARN_USER,
    SEED_QUESTION_SYSTEM,
    SEED_QUESTION_USER,
)

logger = logging.getLogger(__name__)

SEED_MAX_RETRIES = 3
BACKOFF_BASE_SECONDS = 1.5

RETRY_NUDGE = (
    "\n\nYOUR PREVIOUS ATTEMPT FAILED VALIDATION: {reason}. "
    "Return ONLY the corrected JSON object, no prose, no markdown fences."
)


class SeedGenerationError(RuntimeError):
    """All retries exhausted for one item - the CLI logs and moves on."""


async def _generate_validated(system: str, user: str, validate) -> dict:
    """One logical item = up to SEED_MAX_RETRIES gateway calls."""
    reason = None
    for attempt in range(SEED_MAX_RETRIES):
        prompt = user + (RETRY_NUDGE.format(reason=reason) if reason else "")
        try:
            raw = await ask_ai(system, prompt)
            return validate(parse_json(raw))
        except SeedValidationError as exc:
            reason = str(exc)
        except Exception as exc:                          # noqa: BLE001
            reason = f"invalid JSON ({exc})"
        logger.warning("seed retry %d/%d: %s",
                       attempt + 1, SEED_MAX_RETRIES, reason)
        await asyncio.sleep(BACKOFF_BASE_SECONDS * (2 ** attempt))
    raise SeedGenerationError(reason or "unknown validation failure")


async def generate_learn_explainer(
    topic_title: str, subtopic_name: str, question_kind: str
) -> dict:
    """One Learn explainer (what/when/how + exactly 5 worked examples)."""
    return await _generate_validated(
        SEED_LEARN_SYSTEM,
        SEED_LEARN_USER.format(
            topic=topic_title, subtopic=subtopic_name, kind=question_kind,
        ),
        validate_learn_body,
    )


async def generate_seed_question(
    topic_title: str,
    subtopic_name: str,
    difficulty: str,
    question_kind: str,
    existing_statements: List[str],
    existing_norms: Set[str],
) -> dict:
    """One bank question. Dedupe is enforced twice: the differentiation
    block steers the model, the normalized-signature check catches
    anything that slips through (a dedupe hit counts as a retry)."""

    def _validate(parsed: dict) -> dict:
        out = validate_question_body(parsed, question_kind)
        if is_duplicate(out["body"]["question"], existing_norms):
            raise SeedValidationError(
                "duplicate of an existing question in this set")
        return out

    result = await _generate_validated(
        SEED_QUESTION_SYSTEM,
        SEED_QUESTION_USER.format(
            topic=topic_title,
            subtopic=subtopic_name,
            difficulty=difficulty,
            kind=question_kind,
            existing=statements_for_prompt(existing_statements),
        ),
        _validate,
    )
    # keep the rolling dedupe state current for the NEXT question
    existing_statements.append(result["body"]["question"])
    existing_norms.add(normalize_statement(result["body"]["question"]))
    return result
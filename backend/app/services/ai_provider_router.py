# backend/app/services/ai_provider_router.py
"""
The single AI gateway. Every live-AI (Type-B) call routes through here so
provider rotation, fallback, and cost control live in ONE place.

complete()     -> tries the configured providers in order, returns the first
                  success; raises ProviderUnavailable if none are set up or all fail.
score_answer() -> uses complete() + JSON parsing to grade an attempt, and falls
                  back to a deterministic local heuristic when AI is unavailable
                  (so the learning loop always works, even with no API keys).
"""
import json
import re
from typing import Optional

from app.config import settings
from app.services import ai_providers, prompts


class ProviderUnavailable(Exception):
    """Raised when no AI provider is configured or all configured ones failed."""


def _enabled_providers() -> list[str]:
    enabled = []
    for name in settings.AI_PROVIDER_ORDER:
        spec = ai_providers.PROVIDERS.get(name)
        if not spec:
            continue
        _fn, key_attr = spec
        if not getattr(settings, key_attr, ""):
            continue
        # Respect the admin kill-switch (lazy import to avoid a cycle).
        from app.services import provider_admin_service
        if not provider_admin_service.is_enabled(name):
            continue
        enabled.append(name)
    return enabled


async def complete(system: str, user: str) -> str:
    """Try each configured provider in order; return the first non-empty reply."""
    last_error: Optional[Exception] = None
    for name in _enabled_providers():
        fn, _ = ai_providers.PROVIDERS[name]
        try:
            text = await fn(system, user)
            if text and text.strip():
                return text.strip()
        except Exception as exc:  # noqa: BLE001 - rotate to the next provider
            last_error = exc
            continue
    raise ProviderUnavailable(
        str(last_error) if last_error else "No AI providers are configured (set an API key)."
    )


# --- JSON helpers -----------------------------------------------------------
def parse_json(text: str) -> dict:
    """Extract a JSON object from a model reply, tolerating ```json fences."""
    cleaned = re.sub(r"```(?:json)?|```", "", text).strip()
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end != -1:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


# --- answer scoring ---------------------------------------------------------
def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _local_score(question_text: str, model_answer: str, student_answer: str) -> dict:
    """Deterministic keyword-overlap fallback (used when AI is unavailable)."""
    student = _tokens(student_answer)
    if not student:
        return {"score": 0, "feedback": "No answer was submitted. Give it a try — even a partial attempt helps."}
    model = _tokens(model_answer) - _tokens(question_text)
    if model:
        overlap = len(student & model) / len(model)
        score = max(1, min(10, round(overlap * 10)))
    else:
        score = 7 if len(student) >= 8 else 4
    if score >= 8:
        fb = "Strong answer — you covered the key ideas clearly."
    elif score >= 5:
        fb = "Partially correct. You've got the main idea; tighten up the details and edge cases."
    else:
        fb = "Needs work. Revisit the concept card, then focus on the core idea the question is testing."
    return {"score": score, "feedback": fb}


async def score_answer(
    question_text: str, model_answer: Optional[str], student_answer: str
) -> dict:
    """Grade a student answer 0-10 via LLM; fall back to the local heuristic."""
    try:
        text = await complete(prompts.scoring_system(), prompts.scoring_user(question_text, model_answer, student_answer))
        data = parse_json(text)
        score = int(max(0, min(10, int(data["score"]))))
        feedback = str(data.get("feedback") or "").strip() or "Scored."
        return {"score": score, "feedback": feedback}
    except (ProviderUnavailable, KeyError, ValueError, json.JSONDecodeError):
        return _local_score(question_text, model_answer or "", student_answer)


__all__ = ["complete", "score_answer", "parse_json", "ProviderUnavailable"]
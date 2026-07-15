# FILE: app/services/copilot_service.py
# BATCH 20 / v11 Phase 13 (new) - The AI coding copilot: explain / suggest /
# fix / review. Bounded Type-B per the v11 cost architecture:
#   * hard daily cap per student (COPILOT_DAILY_CAP, default 30)
#   * responses CACHED by normalized error signature — the same NameError
#     costs one call platform-wide, not one per student
#   * inputs truncated (code <=4000 chars, error <=1000) — bounded prompts
#   * fix returns a suggestion diff, NEVER auto-applied (frontend shows it)
# Gateway convention (non-negotiable):
#   from app.services.ai_provider_router import complete as ask_ai

from __future__ import annotations

import hashlib
import inspect
import re
from collections import OrderedDict
from datetime import date
from typing import Optional

from fastapi import HTTPException

from app.config import settings
from app.services.ai_provider_router import complete as ask_ai

MODES = ("explain", "suggest", "fix", "review")

_CACHE: "OrderedDict[str, str]" = OrderedDict()
_CACHE_MAX = 500
_DAILY: dict = {}  # (user_id, iso_date) -> count  (in-memory; resets on boot)

SYSTEM = ("You are the ATLAS Live Lab coding copilot for Indian B.Tech "
          "students working in a browser Python (Pyodide) notebook. Be "
          "concise, concrete, and teach — never just hand over the answer. "
          "Plain text, no markdown headers.")

PROMPTS = {
    "explain": ("Explain what this code does and, if an error is shown, "
                "exactly why it happens and the concept behind it.\n\n"
                "CODE:\n{code}\n\nERROR:\n{error}\n\nQUESTION: {question}"),
    "suggest": ("The student is mid-lab. Dataset shape: {dataset_shape}. "
                "Their code so far:\n{code}\n\nGoal/question: {question}\n\n"
                "Give the single most useful NEXT STEP (2-4 sentences + at "
                "most 3 lines of example code). Do not solve the whole lab."),
    "fix": ("This code fails. Return the corrected snippet followed by ONE "
            "line starting with 'WHY: ' explaining the root cause. Change "
            "as little as possible.\n\nCODE:\n{code}\n\nERROR:\n{error}"),
    "review": ("The student completed the lab. Review their notebook: 2 "
               "strengths, 2 concrete improvements, and one interview "
               "question this lab prepares them for.\n\nCODE:\n{code}"),
}


def _cap() -> int:
    return int(getattr(settings, "COPILOT_DAILY_CAP", 30) or 30)


def _spend(user_id: str) -> int:
    """Raise 429 at the cap; return calls left AFTER this one."""
    key = (user_id, date.today().isoformat())
    used = _DAILY.get(key, 0)
    if used >= _cap():
        raise HTTPException(status_code=429,
                            detail=f"Copilot daily cap reached "
                                   f"({_cap()}/day). Resets at midnight.")
    _DAILY[key] = used + 1
    return _cap() - _DAILY[key]


def _refund(user_id: str) -> None:
    key = (user_id, date.today().isoformat())
    if _DAILY.get(key, 0) > 0:
        _DAILY[key] -= 1


def error_signature(error: str) -> str:
    """Normalize an error so equivalent failures share one cache entry:
    drop line numbers, hex addresses, quoted names' variability is kept."""
    sig = re.sub(r"line \d+", "line N", error or "")
    sig = re.sub(r"0x[0-9a-fA-F]+", "0xADDR", sig)
    sig = re.sub(r"\s+", " ", sig).strip().lower()
    return sig[-300:]  # the tail carries the actual exception


def _cache_key(mode: str, code: str, error: str, question: str) -> str:
    if mode in ("explain", "fix") and error:
        basis = f"{mode}|{error_signature(error)}"
    else:
        basis = f"{mode}|{(code or '')[:800]}|{question or ''}"
    return hashlib.sha256(basis.encode()).hexdigest()


def _cache_put(key: str, value: str) -> None:
    _CACHE[key] = value
    _CACHE.move_to_end(key)
    while len(_CACHE) > _CACHE_MAX:
        _CACHE.popitem(last=False)


async def _call_ai(prompt: str) -> str:
    attempts = (lambda: ask_ai(prompt, system=SYSTEM),
                lambda: ask_ai(prompt=prompt, system=SYSTEM),
                lambda: ask_ai(SYSTEM, prompt),
                lambda: ask_ai(f"{SYSTEM}\n\n{prompt}"))
    last = None
    for attempt in attempts:
        try:
            result = attempt()
            if inspect.isawaitable(result):
                result = await result
            if result is not None:
                return result if isinstance(result, str) else str(result)
        except TypeError as exc:
            last = exc
    raise HTTPException(status_code=502, detail=f"AI gateway failed: {last}")


async def run(user_id: str, mode: str,
              code: Optional[str] = None, error: Optional[str] = None,
              question: Optional[str] = None,
              dataset_shape: Optional[str] = None) -> dict:
    if mode not in MODES:
        raise HTTPException(status_code=422,
                            detail=f"mode must be one of {MODES}")
    code = (code or "")[:4000]
    error = (error or "")[:1000]
    question = (question or "")[:500]
    dataset_shape = (dataset_shape or "unknown")[:300]

    key = _cache_key(mode, code, error, question)
    if key in _CACHE:
        _CACHE.move_to_end(key)
        return {"mode": mode, "answer": _CACHE[key], "cached": True,
                "calls_left_today": max(0, _cap() - _DAILY.get(
                    (user_id, date.today().isoformat()), 0))}

    left = _spend(user_id)
    prompt = PROMPTS[mode].format(code=code or "(none)",
                                  error=error or "(none)",
                                  question=question or "(none)",
                                  dataset_shape=dataset_shape)
    try:
        answer = await _call_ai(prompt)
    except HTTPException:
        _refund(user_id)  # a failed gateway call never burns the cap
        raise
    _cache_put(key, answer)
    return {"mode": mode, "answer": answer, "cached": False,
            "calls_left_today": left}
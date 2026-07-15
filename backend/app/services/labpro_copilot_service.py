# backend/app/services/labpro_copilot_service.py
"""
ATLAS AI 4.0 - v12 Live Lab Pro: copilot (explain / suggest / fix / review).

Cost discipline (locked, carried from v11):
  * cache-first: the answer is keyed by sha256(action|env|normalized
    code|error). Same broken code + same traceback -> served FREE from
    labpro_copilot_cache. The cache compounds exactly like the question
    bank.
  * cache MISS -> EXACTLY ONE AI call through the gateway alias, bounded
    by a per-user daily cap (COPILOT_DAILY_CAP). Fix suggestions are
    returned as text; the client NEVER auto-applies them.
"""

import hashlib
import json
import logging
import re
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab_pro import LabProCopilotCache, LabProCopilotUsage
from app.services.ai_provider_router import complete as ask_ai, parse_json
from app.config import settings
from app.prompts import LABPRO_COPILOT_SYSTEM, LABPRO_COPILOT_USER

logger = logging.getLogger(__name__)

_WS_RE = re.compile(r"\s+")


def _signature(action: str, env: str, code: str, error: Optional[str]) -> str:
    """Whitespace-normalized content signature - trivial reformatting of
    the same broken code still hits the cache."""
    norm = _WS_RE.sub(" ", code.strip())
    err = _WS_RE.sub(" ", (error or "").strip())
    raw = f"{action}|{env}|{norm}|{err}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def _usage_row(
    db: AsyncSession, user_id: str
) -> LabProCopilotUsage:
    today = date.today()
    row = (
        await db.execute(
            select(LabProCopilotUsage).where(
                LabProCopilotUsage.user_id == user_id,
                LabProCopilotUsage.day == today,
            )
        )
    ).scalars().first()
    if row is None:
        row = LabProCopilotUsage(user_id=user_id, day=today, used=0)
        db.add(row)
        await db.flush()
    return row


def _clean_response(action: str, parsed: dict) -> dict:
    """Deterministic shape guard on LLM output."""
    fixed = parsed.get("fixed_code")
    return {
        "explanation": str(parsed.get("explanation", ""))[:4_000],
        "suggestion": str(parsed.get("suggestion", ""))[:2_000],
        "fixed_code": (str(fixed)[:10_000] if fixed and action == "fix"
                       else None),
    }


async def run_copilot(
    db: AsyncSession,
    user_id: str,
    action: str,
    code: str,
    error_text: Optional[str],
    goal: Optional[str],
    env: str,
) -> dict:
    cap = int(getattr(settings, "COPILOT_DAILY_CAP", 40))
    usage = await _usage_row(db, user_id)
    key = _signature(action, env, code, error_text)

    # 1. cache hit -> free, does not consume the cap
    cached = (
        await db.execute(
            select(LabProCopilotCache).where(
                LabProCopilotCache.cache_key == key
            )
        )
    ).scalars().first()
    if cached is not None:
        cached.hit_count += 1
        await db.commit()
        body = (cached.response_json if isinstance(cached.response_json, dict)
                else json.loads(cached.response_json))
        return {"action": action, **body, "cached": True,
                "remaining_today": max(0, cap - usage.used)}

    # 2. cap check BEFORE the live call
    if usage.used >= cap:
        raise PermissionError(
            f"Daily copilot limit reached ({cap}). Resets tomorrow - "
            f"cached answers remain free."
        )

    # 3. the ONE AI call (Type B), then persist forever
    raw = await ask_ai(
        LABPRO_COPILOT_SYSTEM,
        LABPRO_COPILOT_USER.format(
            action=action, env=env,
            code=code[:30_000],
            error_text=(error_text or "none")[:8_000],
            goal=(goal or "not stated")[:1_000],
        ),
    )
    try:
        parsed = parse_json(raw)
    except Exception:                                    # noqa: BLE001
        logger.warning("copilot parse failed (action=%s)", action)
        parsed = {"explanation": "The assistant response could not be "
                                 "parsed - please try once more.",
                  "suggestion": "", "fixed_code": None}

    body = _clean_response(action, parsed)
    usage.used += 1
    db.add(LabProCopilotCache(cache_key=key, action=action,
                              response_json=body))
    await db.commit()
    return {"action": action, **body, "cached": False,
            "remaining_today": max(0, cap - usage.used)}
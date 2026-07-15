# backend/app/services/provider_admin_service.py
"""
Admin surface for AI providers: health cards + kill-switch + a live ping.

The kill-switch state is an in-process set of disabled provider names. The AI
gateway (ai_provider_router) consults `is_enabled()` so a killed provider drops
out of the rotation immediately, without touching API keys or config.

super_admin ONLY (see app/routers/admin/providers.py).
"""
from __future__ import annotations

from typing import Optional

from app.config import settings
from app.services import ai_providers

# Providers the admin has manually killed. In-process only — a restart clears it,
# which is the intended "panic switch" behaviour (config/keys stay untouched).
_DISABLED: set[str] = set()


def is_enabled(name: str) -> bool:
    """True unless the provider has been killed via the admin switch."""
    return name not in _DISABLED


def _is_configured(name: str) -> bool:
    spec = ai_providers.PROVIDERS.get(name)
    if not spec:
        return False
    _fn, key_attr = spec
    return bool(getattr(settings, key_attr, ""))


def health_cards() -> list[dict]:
    """One card per known provider, in the configured rotation order first."""
    order = list(settings.AI_PROVIDER_ORDER)
    names = order + [n for n in ai_providers.PROVIDERS if n not in order]

    cards = []
    for name in names:
        configured = _is_configured(name)
        enabled = is_enabled(name)
        cards.append(
            {
                "name": name,
                "configured": configured,
                "enabled": enabled,
                # in rotation only if it has a key AND hasn't been killed
                "in_rotation": configured and enabled,
                "order": order.index(name) if name in order else None,
            }
        )
    return cards


def set_enabled(provider_name: str, enabled: bool) -> dict:
    """Flip the kill-switch for one provider. Returns the resulting card."""
    if provider_name not in ai_providers.PROVIDERS:
        return {"name": provider_name, "error": "unknown provider"}

    if enabled:
        _DISABLED.discard(provider_name)
    else:
        _DISABLED.add(provider_name)

    return {
        "name": provider_name,
        "enabled": is_enabled(provider_name),
        "configured": _is_configured(provider_name),
        "in_rotation": _is_configured(provider_name) and is_enabled(provider_name),
    }


async def ping_gateway(provider: Optional[str] = None) -> dict:
    """One tiny live gateway call to confirm the rotation is answering."""
    # Imported here to avoid a circular import (the router imports this module).
    from app.services import ai_provider_router

    system = "You are a health check. Reply with the single word: pong."
    user = "ping"
    try:
        reply = await ai_provider_router.complete(system, user)
        return {"ok": True, "provider_hint": provider, "reply": reply[:200]}
    except ai_provider_router.ProviderUnavailable as exc:
        return {"ok": False, "provider_hint": provider, "error": str(exc)}


__all__ = ["health_cards", "set_enabled", "ping_gateway", "is_enabled"]

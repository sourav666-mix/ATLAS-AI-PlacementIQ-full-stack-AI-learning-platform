# FILE: tests/helpers.py
# BATCH 18 (new) - Shared helpers for the v10 critical-path suite.
# The suite discovers routes and columns defensively (same pattern as
# Batches 11-17) so it runs against the real app without hardcoding
# every path/payload spelling. Hard asserts on invariants; loud skips
# (naming exactly what was not found) when a surface is absent.

from __future__ import annotations

from typing import Any, Iterable, Optional


# ---------------------------------------------------------------------------
# Route discovery on the real FastAPI app (version-agnostic)
# ---------------------------------------------------------------------------
def _iter_api_routes(routes, prefix: str = ""):
    """Yield (full_path, methods) across FastAPI versions: flattened APIRoutes
    (<=0.11x), Mount objects, and 0.13x `_IncludedRouter` wrappers that keep
    children on `.original_router.routes` with the prefix on
    `.include_context.prefix`."""
    for route in routes or []:
        # 0.13x include_router wrapper
        original = getattr(route, "original_router", None)
        if original is not None and getattr(original, "routes", None):
            ctx = getattr(route, "include_context", None)
            sub_prefix = prefix + (getattr(ctx, "prefix", "") or "")
            yield from _iter_api_routes(original.routes, sub_prefix)
            continue
        # Mounts / nested routers
        sub = getattr(route, "routes", None)
        if sub:
            sub_prefix = prefix + (getattr(route, "path", "") or "")
            yield from _iter_api_routes(sub, sub_prefix)
            continue
        path = getattr(route, "path", None)
        methods = getattr(route, "methods", None)
        if path and methods:
            yield prefix + path, methods


def find_route(app, method: str, *substrings: str) -> Optional[str]:
    """Return the first route path whose lowercase path contains ALL
    substrings and supports `method`. Prefers shorter (more canonical) paths."""
    method = method.upper()
    hits = []
    for path, methods in _iter_api_routes(app.routes):
        low = path.lower()
        if method in methods and all(s in low for s in substrings):
            hits.append(path)
    hits.sort(key=len)
    return hits[0] if hits else None


def fill_path(path: str, **params) -> str:
    for key, value in params.items():
        path = path.replace("{" + key + "}", str(value))
    return path


def request_with_variants(client, method: str, path: str,
                          variants: Iterable[dict], headers=None):
    """Try JSON payload variants until one is not rejected as 422.
    Returns the last response either way."""
    response = None
    for body in variants:
        response = client.request(method, path, json=body, headers=headers)
        if response.status_code != 422:
            return response
    return response


# ---------------------------------------------------------------------------
# Defensive ORM helpers (local copies so tests stand alone)
# ---------------------------------------------------------------------------
def get_base():
    try:
        from app.database import Base  # type: ignore
        return Base
    except Exception:
        from app.models import Base  # type: ignore
        return Base


def model_for_table(table_name: str):
    Base = get_base()
    for mapper in Base.registry.mappers:
        cls = mapper.class_
        if getattr(cls, "__tablename__", None) == table_name:
            return cls
    return None


def col(model, *candidates):
    for name in candidates:
        attr = getattr(model, name, None)
        if attr is not None:
            return attr
    return None


def row_get(obj: Any, *candidates, default=None):
    for name in candidates:
        if obj is not None and hasattr(obj, name):
            value = getattr(obj, name)
            if value is not None:
                return value
    return default


def set_first(obj, value, *candidates) -> bool:
    for name in candidates:
        if hasattr(obj, name):
            setattr(obj, name, value)
            return True
    return False


def token_from(payload: dict) -> Optional[str]:
    for key in ("access_token", "token", "jwt", "accessToken"):
        if isinstance(payload, dict) and payload.get(key):
            return payload[key]
    data = payload.get("data") if isinstance(payload, dict) else None
    if isinstance(data, dict):
        return token_from(data)
    return None
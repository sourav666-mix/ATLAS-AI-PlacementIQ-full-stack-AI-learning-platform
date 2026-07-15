# FILE: app/services/admin_common.py
# BATCH 16 (new) - Shared defensive helpers for the admin content/analytics/providers surface.
#
# Why this file exists:
#   Batch 16 services must work against the ORM models delivered in Batches 1-3
#   WITHOUT depending on exact class names. We resolve models by __tablename__
#   from the SQLAlchemy registry, read/write columns defensively, and adapt to
#   whatever signature audit_service.log_admin_action() was shipped with in
#   Batch 15. This is the same "defensive attribute reading" pattern used in
#   Batches 11-15.

from __future__ import annotations

import inspect
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import inspect as sa_inspect

logger = logging.getLogger("atlas.admin")

# ---------------------------------------------------------------------------
# Base resolution (database.py in Batch 1 defines Base; fall back to models pkg)
# ---------------------------------------------------------------------------
try:
    from app.database import Base  # type: ignore
except Exception:  # pragma: no cover
    from app.models import Base  # type: ignore


# ---------------------------------------------------------------------------
# Model resolution by table name (never by class name)
# ---------------------------------------------------------------------------
def model_for_table(table_name: str):
    """Return the ORM class mapped to `table_name`, or None."""
    try:
        for mapper in Base.registry.mappers:
            cls = mapper.class_
            if getattr(cls, "__tablename__", None) == table_name:
                return cls
    except Exception as exc:  # pragma: no cover
        logger.warning("model_for_table(%s) failed: %s", table_name, exc)
    return None


def require_model(table_name: str):
    """Resolve a model or raise a clear 500 so the admin sees the real problem."""
    model = model_for_table(table_name)
    if model is None:
        raise HTTPException(
            status_code=500,
            detail=f"ORM model for table '{table_name}' not found in registry. "
                   f"Check app/models is fully imported in main.py.",
        )
    return model


# ---------------------------------------------------------------------------
# Defensive column access
# ---------------------------------------------------------------------------
def col(model, *candidates):
    """Return the first mapped column attribute that exists on `model`."""
    for name in candidates:
        attr = getattr(model, name, None)
        if attr is not None:
            return attr
    return None


def row_get(obj: Any, *candidates, default=None):
    """Return the first present attribute VALUE on an ORM row / object."""
    for name in candidates:
        if obj is not None and hasattr(obj, name):
            val = getattr(obj, name)
            if val is not None:
                return val
    return default


def _json_safe(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="ignore")
    return value


def to_dict(row) -> dict:
    """Serialize an ORM row to a JSON-safe dict of its column attributes."""
    if row is None:
        return {}
    try:
        mapper = sa_inspect(row).mapper
        return {c.key: _json_safe(getattr(row, c.key)) for c in mapper.column_attrs}
    except Exception:
        # Fallback: public non-callable attrs
        return {
            k: _json_safe(v)
            for k, v in vars(row).items()
            if not k.startswith("_")
        }


def column_names(model) -> set:
    try:
        return {c.key for c in sa_inspect(model).mapper.column_attrs}
    except Exception:
        return set()


def apply_fields(row, data: dict) -> dict:
    """Set only the keys that are real columns on the row. Returns what was applied."""
    cols = column_names(type(row))
    applied = {}
    for key, value in (data or {}).items():
        if key in cols:
            setattr(row, key, value)
            applied[key] = _json_safe(value)
    return applied


# ---------------------------------------------------------------------------
# Audit adapter — audit_log on EVERY admin write (non-negotiable, Batch 15 rule)
# Adapts to whatever signature log_admin_action() shipped with.
# ---------------------------------------------------------------------------
async def audit(db, admin, action: str, target_table: str,
                target_id: Optional[str] = None, meta: Optional[dict] = None) -> None:
    try:
        from app.services import audit_service
        fn = getattr(audit_service, "log_admin_action", None)
        if fn is None:
            logger.error("AUDIT MISSING: audit_service.log_admin_action not found "
                         "(action=%s table=%s id=%s)", action, target_table, target_id)
            return

        admin_id = row_get(admin, "id")
        candidates = {
            "db": db, "session": db,
            "admin": admin, "admin_user": admin, "actor": admin, "current_admin": admin,
            "admin_id": admin_id, "actor_id": admin_id, "user_id": admin_id,
            "action": action,
            "entity": target_table, "entity_type": target_table,
            "target_table": target_table, "table": target_table,
            "table_name": target_table, "resource": target_table,
            "entity_id": target_id, "target_id": target_id,
            "resource_id": target_id, "row_id": target_id, "record_id": target_id,
            "meta": meta, "details": meta, "detail": meta,
            "payload": meta, "extra": meta, "data": meta, "changes": meta,
        }
        params = inspect.signature(fn).parameters
        kwargs = {}
        for p in params.values():
            if p.name in ("args", "kwargs"):
                continue
            if p.name in candidates and candidates[p.name] is not None:
                kwargs[p.name] = candidates[p.name]
            elif p.default is inspect.Parameter.empty and p.name not in kwargs:
                # Required param we don't recognize -> best-effort positional later
                pass

        try:
            result = fn(**kwargs)
            if inspect.isawaitable(result):
                await result
            return
        except TypeError:
            # Last-resort positional call: (db, admin_id, action, table, id)
            result = fn(db, admin_id, action, target_table, target_id)
            if inspect.isawaitable(result):
                await result
            return
    except Exception as exc:
        # Never break an admin write because the audit adapter mismatched,
        # but log LOUDLY so it is fixed immediately.
        logger.error("AUDIT WRITE FAILED (action=%s table=%s id=%s): %s",
                     action, target_table, target_id, exc)


# ---------------------------------------------------------------------------
# AI gateway adapter — router exports `complete` (NOT ask_ai). Convention:
#   from app.services.ai_provider_router import complete as ask_ai, parse_json
# Signatures have varied per batch, so we adapt.
# ---------------------------------------------------------------------------
from app.services.ai_provider_router import complete as ask_ai, parse_json  # noqa: E402,F401


async def call_ai(prompt: str, system: str = "") -> str:
    """One live AI call through the gateway, tolerant of `complete`'s signature."""
    attempts = (
        lambda: ask_ai(prompt, system=system),
        lambda: ask_ai(prompt=prompt, system=system),
        lambda: ask_ai(system, prompt),
        lambda: ask_ai(f"{system}\n\n{prompt}".strip()),
        lambda: ask_ai(messages=[{"role": "system", "content": system},
                                 {"role": "user", "content": prompt}]),
    )
    last_err: Optional[Exception] = None
    for attempt in attempts:
        try:
            result = attempt()
            if inspect.isawaitable(result):
                result = await result
            if result is not None:
                return result if isinstance(result, str) else str(result)
        except TypeError as exc:
            last_err = exc
            continue
    raise HTTPException(status_code=502,
                        detail=f"AI gateway call failed: {last_err}")
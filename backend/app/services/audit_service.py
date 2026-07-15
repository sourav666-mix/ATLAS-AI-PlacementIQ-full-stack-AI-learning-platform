# audit_service.py - log_admin_action() on every admin write
# backend/app/services/audit_service.py
"""audit_service — log_admin_action() on EVERY admin write.

Spec rule (Project Guide §8): "Every admin write is recorded in audit_log."
This is deliberately fire-and-forget: an audit failure must never roll back the
admin's actual write, so it commits on the caller's session and swallows its
own errors (they're logged to the app log instead).
"""
from __future__ import annotations

import json
import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

# --- INTEGRATION POINT -------------------------------------------------------
from app.models.audit_log import AuditLog  # Batch 2 model
# Expected columns: id, admin_id, action, entity, entity_id, details, created_at
# (missing columns are skipped defensively below)
# -----------------------------------------------------------------------------

logger = logging.getLogger(__name__)


async def log_admin_action(db: AsyncSession, admin_id: str, action: str,
                           entity: str, entity_id: str | None = None,
                           details: dict | None = None) -> None:
    """Record one admin write. Never raises."""
    try:
        payload = json.dumps(details or {}, default=str)[:4000]
        kwargs = {"id": str(uuid.uuid4()), "admin_id": admin_id,
                  "action": action, "entity": entity}
        # set optional columns only if the model has them
        for col, val in (("entity_id", entity_id), ("details", payload)):
            if hasattr(AuditLog, col):
                kwargs[col] = val
        db.add(AuditLog(**kwargs))
        await db.commit()
    except Exception as exc:  # noqa: BLE001 — audit must never break the write
        logger.error("audit_log write failed: %s", exc)
        try:
            await db.rollback()
        except Exception:
            pass
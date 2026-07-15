# providers.py - AI provider health + kill-switch
# FILE: app/routers/admin/providers.py
# BATCH 16 (new) - AI provider health + kill-switch (super_admin ONLY —
# per v10 Project Guide §8, college_admin has no providers surface at all).
# Every toggle is written to audit_log.

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.services import provider_admin_service as providers
from app.services.admin_auth_service import require_super_admin
from app.services.admin_common import audit

router = APIRouter(prefix="/admin/providers", tags=["admin-providers"])


@router.get("")
async def get_providers(admin=Depends(require_super_admin)):
    return providers.health_cards()


@router.post("/{provider_name}/kill")
async def kill_provider(provider_name: str,
                        db: AsyncSession = Depends(get_db),
                        admin=Depends(require_super_admin)):
    result = providers.set_enabled(provider_name, enabled=False)
    await audit(db, admin, "providers.kill", "ai_providers",
                provider_name, result)
    return result


@router.post("/{provider_name}/enable")
async def enable_provider(provider_name: str,
                          db: AsyncSession = Depends(get_db),
                          admin=Depends(require_super_admin)):
    result = providers.set_enabled(provider_name, enabled=True)
    await audit(db, admin, "providers.enable", "ai_providers",
                provider_name, result)
    return result


@router.post("/ping")
async def ping(provider: Optional[str] = Query(default=None),
               admin=Depends(require_super_admin)):
    """One tiny live gateway call — confirms the rotation (or one provider,
    if the router's `complete` accepts a provider hint) is answering."""
    return await providers.ping_gateway(provider=provider)
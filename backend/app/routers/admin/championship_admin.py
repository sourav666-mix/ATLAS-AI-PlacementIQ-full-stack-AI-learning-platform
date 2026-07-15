# championship_admin.py - [NEW] build/schedule/monitor/analyze/podium/publish
# backend/app/routers/admin/championship_admin.py
"""Weekly Championship — admin endpoints.

  POST /admin/championship                        -> create (draft)
  PUT  /admin/championship/{id}                   -> edit paper/metadata (draft only)
  POST /admin/championship/{id}/schedule           -> draft → scheduled
  POST /admin/championship/{id}/go-live            -> scheduled → live
  POST /admin/championship/{id}/close              -> live → closed
  POST /admin/championship/{id}/analyze            -> batch AI analysis (ONE call)
  PUT  /admin/championship/{id}/podium             -> select 1st/2nd/3rd
  POST /admin/championship/{id}/publish            -> closed → published
  GET  /admin/championship/{id}/monitor            -> live participants
  GET  /admin/championship/{id}/results            -> ranked results console
  GET  /admin/championship                        -> list all (scoped by role)

Gated by app.services.admin_auth_service.require_admin_role.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.admin_auth_service import require_admin_role as _real_admin_gate
from app.schemas.championship import (
    AdminChampionshipRow,
    ChampionshipCreate,
    ChampionshipUpdate,
    LiveMonitorResponse,
    PodiumSelect,
    ResultsConsoleResponse,
)
from app.services import championship_admin_service

router = APIRouter(prefix="/admin/championship", tags=["Championship (Admin)"])

require_admin = _real_admin_gate


# ── CRUD ─────────────────────────────────────────────────────────────────────
@router.post("", response_model=AdminChampionshipRow)
@router.post("/", response_model=AdminChampionshipRow, include_in_schema=False)
async def create_championship(
    payload: ChampionshipCreate,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_admin),
):
    c = await championship_admin_service.create(db, actor, payload)
    paper = c.question_paper_json or []
    return AdminChampionshipRow(
        id=c.id, title=c.title or "", status=c.status,
        college_id=c.college_id, starts_at=c.starts_at,
        duration_secs=c.duration_secs,
        question_count=len(paper) if isinstance(paper, list) else 0,
        created_at=getattr(c, "created_at", None),
    )


@router.put("/{champ_id}", response_model=AdminChampionshipRow)
async def update_championship(
    champ_id: str,
    payload: ChampionshipUpdate,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_admin),
):
    c = await championship_admin_service.update(db, actor, champ_id, payload)
    paper = c.question_paper_json or []
    return AdminChampionshipRow(
        id=c.id, title=c.title or "", status=c.status,
        college_id=c.college_id, starts_at=c.starts_at,
        duration_secs=c.duration_secs,
        question_count=len(paper) if isinstance(paper, list) else 0,
        created_at=getattr(c, "created_at", None),
    )


@router.get("", response_model=list[AdminChampionshipRow])
async def list_championships(
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_admin),
):
    return await championship_admin_service.list_championships(db, actor)


# ── state transitions ────────────────────────────────────────────────────────
@router.post("/{champ_id}/schedule")
async def schedule(champ_id: str, db: AsyncSession = Depends(get_db),
                   actor: dict = Depends(require_admin)):
    c = await championship_admin_service.transition(db, actor, champ_id, "scheduled")
    return {"id": c.id, "status": c.status}


@router.post("/{champ_id}/go-live")
async def go_live(champ_id: str, db: AsyncSession = Depends(get_db),
                  actor: dict = Depends(require_admin)):
    c = await championship_admin_service.transition(db, actor, champ_id, "live")
    return {"id": c.id, "status": c.status}


@router.post("/{champ_id}/close")
async def close(champ_id: str, db: AsyncSession = Depends(get_db),
                actor: dict = Depends(require_admin)):
    c = await championship_admin_service.transition(db, actor, champ_id, "closed")
    return {"id": c.id, "status": c.status}


@router.post("/{champ_id}/publish")
async def publish(champ_id: str, db: AsyncSession = Depends(get_db),
                  actor: dict = Depends(require_admin)):
    c = await championship_admin_service.transition(db, actor, champ_id, "published")
    return {"id": c.id, "status": c.status}


# ── monitor + results + analysis + podium ────────────────────────────────────
@router.get("/{champ_id}/monitor", response_model=LiveMonitorResponse)
async def live_monitor(champ_id: str, db: AsyncSession = Depends(get_db),
                       actor: dict = Depends(require_admin)):
    return await championship_admin_service.monitor(db, actor, champ_id)


@router.get("/{champ_id}/results", response_model=ResultsConsoleResponse)
async def results_console(champ_id: str, db: AsyncSession = Depends(get_db),
                          actor: dict = Depends(require_admin)):
    return await championship_admin_service.results_console(db, actor, champ_id)


@router.post("/{champ_id}/analyze")
async def batch_analyze(champ_id: str, db: AsyncSession = Depends(get_db),
                        actor: dict = Depends(require_admin)):
    return await championship_admin_service.batch_analyze(db, actor, champ_id)


@router.put("/{champ_id}/podium")
async def set_podium(champ_id: str, payload: PodiumSelect,
                     db: AsyncSession = Depends(get_db),
                     actor: dict = Depends(require_admin)):
    c = await championship_admin_service.set_podium(db, actor, champ_id, payload)
    return {"id": c.id, "podium": c.podium_json}
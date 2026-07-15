# FILE: app/routers/lab.py
# BATCH 20 / v11 Phase 13 (new) - The Live Lab router, endpoint surface per
# the v11 folder structure doc §1.2:
#   GET  /lab                      catalog (Type A)
#   GET  /lab/{lab_id}             starter code + dataset + tasks + session
#   GET  /lab/{lab_id}/tests       hidden test code for the BROWSER runner
#   POST /lab/grade                record in-browser results (NO AI)
#   POST /lab/copilot/explain|suggest|fix|review   bounded Type-B
#   POST /lab/colab-launch         ready-to-run notebook (needs_gpu labs)
#   POST /lab/complete             finalize + points via progress_engine

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.schemas.lab import (ColabLaunch, ColabLaunchResponse,
                             CompleteRequest, CopilotRequest,
                             CopilotResponse, GradeRequest, GradeResult,
                             LabListItem, LabResponse)
from app.services import colab_service, copilot_service, lab_service

# Batch 4 student auth dependency — name resolved defensively (Batch 17 pattern)
try:
    from app.dependencies import get_current_user
except ImportError:  # pragma: no cover
    try:
        from app.dependencies import get_current_active_user as get_current_user
    except ImportError:
        from app.services.auth_service import get_current_user

router = APIRouter(prefix="/lab", tags=["live-lab"])


def _uid(user) -> str:
    return getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else None)


@router.get("", response_model=list[LabListItem])
async def catalog(domain_id: Optional[str] = Query(default=None),
                  db: AsyncSession = Depends(get_db),
                  user=Depends(get_current_user)):
    return await lab_service.list_labs(db, domain_id=domain_id)


@router.get("/{lab_id}", response_model=LabResponse)
async def get_lab(lab_id: str, db: AsyncSession = Depends(get_db),
                  user=Depends(get_current_user)):
    return await lab_service.get_lab(db, _uid(user), lab_id)


@router.get("/{lab_id}/tests")
async def get_hidden_tests(lab_id: str, db: AsyncSession = Depends(get_db),
                           user=Depends(get_current_user)):
    """Test code executes in the student's Pyodide worker, never here."""
    return {"lab_id": lab_id,
            "tests": await lab_service.hidden_tests(db, lab_id)}


@router.post("/grade", response_model=GradeResult)
async def grade(payload: GradeRequest, db: AsyncSession = Depends(get_db),
                user=Depends(get_current_user)):
    return await lab_service.record_grade(
        db, _uid(user), payload.lab_id, payload.tasks_passed,
        payload.code_snapshot,
        [a.model_dump() for a in payload.artifacts] if payload.artifacts
        else None)


def _copilot_endpoint(mode: str):
    async def endpoint(payload: CopilotRequest,
                       user=Depends(get_current_user)) -> CopilotResponse:
        result = await copilot_service.run(
            _uid(user), mode, code=payload.code, error=payload.error,
            question=payload.question, dataset_shape=payload.dataset_shape)
        return CopilotResponse(**result)
    endpoint.__name__ = f"copilot_{mode}"
    return endpoint


for _mode in copilot_service.MODES:
    router.add_api_route(f"/copilot/{_mode}", _copilot_endpoint(_mode),
                         methods=["POST"], response_model=CopilotResponse,
                         name=f"copilot_{_mode}")


@router.post("/colab-launch", response_model=ColabLaunchResponse)
async def colab_launch(payload: ColabLaunch, request: Request,
                       db: AsyncSession = Depends(get_db),
                       user=Depends(get_current_user)):
    api_base = str(request.base_url)
    return await colab_service.launch(db, _uid(user), payload.lab_id,
                                      payload.code, api_base)


@router.post("/complete")
async def complete(payload: CompleteRequest,
                   db: AsyncSession = Depends(get_db),
                   user=Depends(get_current_user)):
    return await lab_service.complete(db, _uid(user), payload.lab_id)
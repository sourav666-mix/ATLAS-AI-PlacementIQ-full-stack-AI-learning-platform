# jobs_admin.py - [NEW] post/edit/expire verified openings + analytics
# backend/app/routers/admin/jobs_admin.py
"""Jobs Board — admin / college-admin posting (role-gated).

  POST /admin/jobs                 -> create a verified posting
  PUT  /admin/jobs/{id}            -> edit
  POST /admin/jobs/{id}/expire     -> archive
  GET  /admin/jobs                 -> my postings (+ saves/applies)
  GET  /admin/jobs/analytics       -> per-posting analytics

--- TEMPORARY AUTH BRIDGE (read me) ----------------------------------------
Dedicated admin auth (admin_users + JWT role claims) is built later in the
Admin Panel session. Until then, `require_poster` gates on a role attribute of
the *current user* so the app still boots and students are firmly blocked
(they have no such role => 403, satisfying "no public posting path").

When the admin auth service lands, replace `require_poster` with that service's
`require_admin_role` dependency — the endpoints below are already written
against the small {id, role, college_id} actor dict it should return.
Until then, populate the board with `scripts/seed_jobs.py`.
----------------------------------------------------------------------------
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.admin_auth_service import require_admin_role
from app.schemas.jobs import (
    AdminJobRow,
    JobPostCreate,
    JobPostUpdate,
    PostingAnalytics,
)
from app.services import jobs_admin_service

router = APIRouter(prefix="/admin/jobs", tags=["Jobs Board (Admin)"])

require_poster = require_admin_role


@router.post("", response_model=AdminJobRow)
@router.post("/", response_model=AdminJobRow, include_in_schema=False)
async def create_job(
    payload: JobPostCreate,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_poster),
):
    posting = await jobs_admin_service.create_posting(db, actor, payload)
    return AdminJobRow(
        id=posting.id, kind=posting.kind, title=posting.title or "",
        company=posting.company or "", visibility=posting.visibility,
        college_id=posting.college_id, status=posting.status,
        deadline=getattr(posting, "deadline", None),
        created_at=getattr(posting, "created_at", None),
    )


@router.get("", response_model=list[AdminJobRow])
async def list_my_jobs(
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_poster),
):
    return await jobs_admin_service.list_postings(db, actor)


@router.get("/analytics", response_model=list[PostingAnalytics])
async def jobs_analytics(
    job_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_poster),
):
    return await jobs_admin_service.analytics(db, actor, job_id)


@router.put("/{job_id}", response_model=AdminJobRow)
async def edit_job(
    job_id: str,
    payload: JobPostUpdate,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_poster),
):
    posting = await jobs_admin_service.update_posting(db, actor, job_id, payload)
    return AdminJobRow(
        id=posting.id, kind=posting.kind, title=posting.title or "",
        company=posting.company or "", visibility=posting.visibility,
        college_id=posting.college_id, status=posting.status,
        deadline=getattr(posting, "deadline", None),
        created_at=getattr(posting, "created_at", None),
    )


@router.post("/{job_id}/expire", response_model=AdminJobRow)
async def expire_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_poster),
):
    posting = await jobs_admin_service.expire_posting(db, actor, job_id)
    return AdminJobRow(
        id=posting.id, kind=posting.kind, title=posting.title or "",
        company=posting.company or "", visibility=posting.visibility,
        college_id=posting.college_id, status=posting.status,
        deadline=getattr(posting, "deadline", None),
        created_at=getattr(posting, "created_at", None),
    )
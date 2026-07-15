# colleges.py - CRUD colleges + CSV bulk-invite + seat tracking
# backend/app/routers/admin/colleges.py
"""Admin — college onboarding, seats, CSV bulk-invite (role-scoped).

  POST /admin/colleges                      -> onboard (super_admin)
  GET  /admin/colleges                      -> list (super: all; college_admin: own)
  GET  /admin/colleges/{id}                 -> detail + seat usage
  PUT  /admin/colleges/{id}                 -> update contract/seats (super_admin)
  POST /admin/colleges/{id}/invite          -> bulk-invite (JSON rows)
  POST /admin/colleges/{id}/invite-csv      -> bulk-invite (CSV file upload)

college_admin may only view + invite into THEIR OWN college. Every write is
recorded in audit_log.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.admin import (
    BulkInviteRequest,
    BulkInviteResponse,
    CollegeCreate,
    CollegeRow,
    CollegeUpdate,
)
from app.services import audit_service, college_service
from app.services.admin_auth_service import require_admin_role, require_super_admin

router = APIRouter(prefix="/admin/colleges", tags=["Admin Colleges"])


def _own_college_or_403(actor: dict, college_id: str) -> None:
    if actor["role"] == "super_admin":
        return
    if actor.get("college_id") != college_id:
        raise HTTPException(403, "College admins can only access their own college")


@router.post("", response_model=CollegeRow)
@router.post("/", response_model=CollegeRow, include_in_schema=False)
async def onboard_college(
    payload: CollegeCreate,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_super_admin),
):
    row = await college_service.create_college(db, payload)
    await audit_service.log_admin_action(
        db, actor["id"], "create", "college", row.id,
        {"name": row.name, "license_seats": row.license_seats})
    return row


@router.get("", response_model=list[CollegeRow])
async def list_colleges(
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_admin_role),
):
    if actor["role"] == "super_admin":
        return await college_service.list_colleges(db)
    if not actor.get("college_id"):
        return []
    return [await college_service.get_college(db, actor["college_id"])]


@router.get("/{college_id}", response_model=CollegeRow)
async def college_detail(
    college_id: str,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_admin_role),
):
    _own_college_or_403(actor, college_id)
    return await college_service.get_college(db, college_id)


@router.put("/{college_id}", response_model=CollegeRow)
async def update_college(
    college_id: str,
    payload: CollegeUpdate,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_super_admin),
):
    row = await college_service.update_college(db, college_id, payload)
    await audit_service.log_admin_action(
        db, actor["id"], "update", "college", college_id,
        payload.model_dump(exclude_unset=True))
    return row


@router.post("/{college_id}/invite", response_model=BulkInviteResponse)
async def bulk_invite_json(
    college_id: str,
    payload: BulkInviteRequest,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_admin_role),
):
    _own_college_or_403(actor, college_id)
    if not payload.rows:
        raise HTTPException(400, "No invite rows supplied")
    result = await college_service.bulk_invite(db, college_id, payload.rows)
    await audit_service.log_admin_action(
        db, actor["id"], "bulk_invite", "college", college_id,
        {"requested": result.requested, "created": result.created,
         "skipped": result.skipped})
    return result


@router.post("/{college_id}/invite-csv", response_model=BulkInviteResponse)
async def bulk_invite_csv(
    college_id: str,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_admin_role),
):
    _own_college_or_403(actor, college_id)
    raw = await file.read()
    rows = college_service.parse_invite_csv(raw)
    if not rows:
        raise HTTPException(400, "CSV contained no valid 'name,email' rows")
    result = await college_service.bulk_invite(db, college_id, rows)
    await audit_service.log_admin_action(
        db, actor["id"], "bulk_invite_csv", "college", college_id,
        {"filename": file.filename, "requested": result.requested,
         "created": result.created, "skipped": result.skipped})
    return result
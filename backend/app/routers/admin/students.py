# students.py - search / view / override any student (role-scoped)
# backend/app/routers/admin/students.py
"""Admin — student management (role-scoped).

  GET  /admin/students?q=&college_id=&limit=  -> search (college_admin: own cohort only)
  GET  /admin/students/{id}                    -> detail
  PUT  /admin/students/{id}                    -> override (super_admin only)

Spec: super_admin can search/view/override ANY account and reset access;
college_admin gets read-only views of THEIR cohort only — they can never see
another cohort (verified in tests) and never get override rights.
"""
from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.admin import StudentOverride, StudentOverrideResult, StudentRow
from app.services import audit_service
from app.services.admin_auth_service import (
    hash_admin_password,
    require_admin_role,
    require_super_admin,
)

router = APIRouter(prefix="/admin/students", tags=["Admin Students"])


def _to_row(u: User) -> StudentRow:
    return StudentRow(
        id=u.id,
        name=getattr(u, "name", "") or "",
        email=getattr(u, "email", "") or "",
        college_id=getattr(u, "college_id", None),
        role=getattr(u, "role", "student") or "student",
        profile_bar_score=getattr(u, "profile_bar_score", None),
        created_at=getattr(u, "created_at", None),
    )


@router.get("", response_model=list[StudentRow])
async def search_students(
    q: str | None = Query(None, description="search name/email"),
    college_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_admin_role),
):
    stmt = select(User)
    # role scoping: college_admin is HARD-locked to their own cohort,
    # regardless of any college_id they pass in the query
    if actor["role"] != "super_admin":
        if not actor.get("college_id"):
            return []
        stmt = stmt.where(User.college_id == actor["college_id"])
    elif college_id:
        stmt = stmt.where(User.college_id == college_id)

    if q:
        like = f"%{q.strip()}%"
        conds = [User.email.ilike(like)]
        if hasattr(User, "name"):
            conds.append(User.name.ilike(like))
        stmt = stmt.where(or_(*conds))

    rows = (await db.execute(stmt.limit(limit))).scalars().all()
    return [_to_row(u) for u in rows]


@router.get("/{student_id}", response_model=StudentRow)
async def student_detail(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_admin_role),
):
    u = (await db.execute(select(User).where(
        User.id == student_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "Student not found")
    if actor["role"] != "super_admin" and \
            getattr(u, "college_id", None) != actor.get("college_id"):
        raise HTTPException(403, "Not in your cohort")
    return _to_row(u)


@router.put("/{student_id}", response_model=StudentOverrideResult)
async def override_student(
    student_id: str,
    payload: StudentOverride,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_super_admin),   # overrides are super-only
):
    u = (await db.execute(select(User).where(
        User.id == student_id))).scalar_one_or_none()
    if not u:
        raise HTTPException(404, "Student not found")

    updated: list[str] = []
    temp_password = None
    if payload.name is not None and hasattr(u, "name"):
        u.name = payload.name
        updated.append("name")
    if payload.college_id is not None and hasattr(u, "college_id"):
        u.college_id = payload.college_id
        updated.append("college_id")
    if payload.reset_password and hasattr(u, "password_hash"):
        temp_password = secrets.token_urlsafe(9)
        u.password_hash = hash_admin_password(temp_password)
        updated.append("password")
    await db.commit()

    await audit_service.log_admin_action(
        db, actor["id"], "override", "user", student_id,
        {"updated": updated})

    return StudentOverrideResult(id=student_id, updated_fields=updated,
                                 temp_password=temp_password)
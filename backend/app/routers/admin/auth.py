# auth.py - POST /admin/login (super_admin / college_admin)
# backend/app/routers/admin/auth.py
"""Admin auth — separate login for the admin panel (admin.atlasai.in).

  POST /admin/login          -> AdminToken (JWT with scope=admin + role claims)
  GET  /admin/me             -> current admin identity
  POST /admin/admins         -> create another admin (super_admin only)

Admin credentials live in admin_users, fully isolated from student auth.
The first super_admin is created with scripts/create_super_admin.py.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.admin_user import AdminUser
from app.schemas.admin import AdminCreate, AdminLogin, AdminMe, AdminToken
from app.services import audit_service
from app.services.admin_auth_service import (
    create_admin_token,
    get_current_admin,
    hash_admin_password,
    require_super_admin,
)
from app.services import admin_auth_service

router = APIRouter(prefix="/admin", tags=["Admin Auth"])


@router.post("/login", response_model=AdminToken)
async def admin_login(payload: AdminLogin, db: AsyncSession = Depends(get_db)):
    admin = await admin_auth_service.authenticate(db, payload.email, payload.password)
    if not admin:
        raise HTTPException(401, "Invalid admin credentials")
    return AdminToken(
        access_token=create_admin_token(admin),
        role=admin.role,
        college_id=getattr(admin, "college_id", None),
        name=getattr(admin, "full_name", "") or "",
    )


@router.get("/me", response_model=AdminMe)
async def admin_me(actor: dict = Depends(get_current_admin)):
    return AdminMe(**{k: actor.get(k) for k in
                       ("id", "email", "name", "role", "college_id")})


@router.post("/admins", response_model=AdminMe)
async def create_admin(
    payload: AdminCreate,
    db: AsyncSession = Depends(get_db),
    actor: dict = Depends(require_super_admin),
):
    if payload.role == "college_admin" and not payload.college_id:
        raise HTTPException(400, "college_admin requires a college_id")
    email = payload.email.strip().lower()
    exists = (await db.execute(select(AdminUser).where(
        AdminUser.email == email))).scalar_one_or_none()
    if exists:
        raise HTTPException(409, "An admin with this email already exists")

    admin = AdminUser(id=str(uuid.uuid4()), email=email,
                      hashed_password=hash_admin_password(payload.password),
                      role=payload.role)
    for col, val in (("full_name", payload.name), ("college_id", payload.college_id)):
        if hasattr(admin, col):
            setattr(admin, col, val)
    db.add(admin)
    await db.commit()
    await db.refresh(admin)

    await audit_service.log_admin_action(
        db, actor["id"], "create", "admin_user", admin.id,
        {"email": email, "role": payload.role, "college_id": payload.college_id})

    return AdminMe(id=admin.id, email=admin.email,
                   name=getattr(admin, "full_name", "") or "",
                   role=admin.role,
                   college_id=getattr(admin, "college_id", None))
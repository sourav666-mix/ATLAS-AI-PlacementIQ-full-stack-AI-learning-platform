# admin_auth_service.py - require_admin_role() / require_super_admin()
# backend/app/services/admin_auth_service.py
"""admin_auth_service — separate admin authentication + THE role gates.

This is the real gate that replaces the temporary bridges shipped in
Batch 12 (jobs_admin.require_poster) and Batch 13 (championship_admin.require_admin).

Admin identity lives in admin_users (NOT the student users table). Admin JWTs
carry {"sub": admin_id, "role": ..., "college_id": ..., "scope": "admin"} —
a student token can never pass these gates because it lacks scope=admin.

Exports:
  authenticate(db, email, password) -> AdminUser | None
  create_admin_token(admin)         -> str
  get_current_admin (dependency)    -> actor dict {id, role, college_id, email, name}
  require_admin_role (dependency)   -> actor (super_admin OR college_admin)
  require_super_admin (dependency)  -> actor (super_admin only)
"""
from __future__ import annotations

import hashlib
import hmac
import os

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db

# --- INTEGRATION POINT -------------------------------------------------------
from app.models.admin_user import AdminUser  # Batch 2 model
# Expected columns: id, email, hashed_password, full_name, role, college_id
# -----------------------------------------------------------------------------

_bearer = HTTPBearer(auto_error=False)


# ── password hashing ─────────────────────────────────────────────────────────
# Prefer the exact same hashing used by student auth (Batch 4) so one policy
# governs both; fall back to a local PBKDF2 if those helpers aren't importable.
def _import_auth_hashers():
    try:
        from app.services.auth_service import hash_password, verify_password  # type: ignore
        return hash_password, verify_password
    except Exception:
        return None, None


_HASH, _VERIFY = _import_auth_hashers()

_PBKDF2_ITER = 200_000


def _pbkdf2_hash(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITER)
    return f"pbkdf2${salt.hex()}${dk.hex()}"


def _pbkdf2_verify(password: str, stored: str) -> bool:
    try:
        _tag, salt_hex, dk_hex = stored.split("$", 2)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode(),
                                 bytes.fromhex(salt_hex), _PBKDF2_ITER)
        return hmac.compare_digest(dk.hex(), dk_hex)
    except Exception:
        return False


def hash_admin_password(password: str) -> str:
    return _HASH(password) if _HASH else _pbkdf2_hash(password)


def verify_admin_password(password: str, stored: str) -> bool:
    if stored.startswith("pbkdf2$"):
        return _pbkdf2_verify(password, stored)
    if _VERIFY:
        try:
            return bool(_VERIFY(password, stored))
        except Exception:
            return False
    return False


# ── JWT ───────────────────────────────────────────────────────────────────────
# admin tokens carry MULTIPLE top-level claims (sub, scope, role, college_id),
# but jwt_utils.create_access_token(subject) only accepts a single string
# subject — passing a whole dict as `subject` used to stringify it into `sub`
# and silently drop scope/role/college_id, so get_current_admin's
# `payload.get("scope") != "admin"` check always failed. Encode directly here
# instead, reusing the same SECRET_KEY/ALGORITHM so jwt_utils.decode_access_token
# (a generic decoder) still reads it back correctly.
def _create_token(claims: dict) -> str:
    from datetime import datetime, timedelta, timezone
    from jose import jwt as jose_jwt
    from app.config import settings

    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {**claims, "iat": now, "exp": expire}
    return jose_jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _decode_token(token: str) -> dict:
    from app.utils import jwt_utils
    for name in ("verify_token", "decode_token", "decode_access_token"):
        fn = getattr(jwt_utils, name, None)
        if fn:
            data = fn(token)
            if not isinstance(data, dict):
                raise HTTPException(401, "Invalid admin token")
            return data
    raise RuntimeError("jwt_utils has no token-decoding function")


def create_admin_token(admin: AdminUser) -> str:
    return _create_token({
        "sub": admin.id,
        "scope": "admin",
        "role": admin.role,
        "college_id": getattr(admin, "college_id", None),
    })


# ── authenticate ─────────────────────────────────────────────────────────────
async def authenticate(db: AsyncSession, email: str, password: str) -> AdminUser | None:
    admin = (await db.execute(select(AdminUser).where(
        AdminUser.email == email.strip().lower()))).scalar_one_or_none()
    if not admin:
        return None
    if not verify_admin_password(password, admin.hashed_password or ""):
        return None
    return admin


# ── dependencies (THE gates) ─────────────────────────────────────────────────
async def get_current_admin(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if credentials is None:
        raise HTTPException(401, "Admin authentication required")
    payload = _decode_token(credentials.credentials)
    if payload.get("scope") != "admin":
        raise HTTPException(403, "Admin token required (student tokens are not valid here)")
    admin = (await db.execute(select(AdminUser).where(
        AdminUser.id == payload.get("sub")))).scalar_one_or_none()
    if not admin:
        raise HTTPException(401, "Admin account not found")
    return {
        "id": admin.id,
        "role": admin.role,
        "college_id": getattr(admin, "college_id", None),
        "email": admin.email,
        "name": getattr(admin, "full_name", "") or "",
    }


async def require_admin_role(actor: dict = Depends(get_current_admin)) -> dict:
    """super_admin OR college_admin — the general admin gate."""
    if actor["role"] not in ("super_admin", "college_admin"):
        raise HTTPException(403, "Admin role required")
    return actor


async def require_super_admin(actor: dict = Depends(get_current_admin)) -> dict:
    if actor["role"] != "super_admin":
        raise HTTPException(403, "Super admin role required")
    return actor
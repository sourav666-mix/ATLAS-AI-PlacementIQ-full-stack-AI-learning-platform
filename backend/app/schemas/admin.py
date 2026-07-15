# admin.py - AdminLogin, CollegeCreate, BulkInvite
# backend/app/schemas/admin.py
"""Admin Panel — schemas (Pydantic v2).

Covers admin auth (separate from student auth), college onboarding with seat
licensing, CSV bulk-invite, and role-scoped student management.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

ADMIN_ROLES = ["super_admin", "college_admin"]


# ── auth ─────────────────────────────────────────────────────────────────────
class AdminLogin(BaseModel):
    # plain str (not EmailStr): this account intentionally uses a non-standard
    # "email" value, so login must accept it as-is rather than validating format.
    email: str
    password: str


class AdminToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    college_id: Optional[str] = None
    name: str = ""


class AdminMe(BaseModel):
    id: str
    email: str
    name: str = ""
    role: str
    college_id: Optional[str] = None


class AdminCreate(BaseModel):
    """Super-admin-only: create another admin account."""
    email: EmailStr
    password: str
    name: str = ""
    role: str = "college_admin"
    college_id: Optional[str] = None       # required when role=college_admin

    @field_validator("role")
    @classmethod
    def _role_ok(cls, v: str) -> str:
        if v not in ADMIN_ROLES:
            raise ValueError(f"role must be one of {ADMIN_ROLES}")
        return v

    @field_validator("password")
    @classmethod
    def _pw_ok(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


# ── colleges ─────────────────────────────────────────────────────────────────
class CollegeCreate(BaseModel):
    name: str
    license_seats: int = Field(50, ge=1)
    plan_domains: list[str] = Field(default_factory=list)   # domains in contract
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None


class CollegeUpdate(BaseModel):
    name: Optional[str] = None
    license_seats: Optional[int] = Field(None, ge=1)
    plan_domains: Optional[list[str]] = None
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None


class CollegeRow(BaseModel):
    id: str
    name: str
    license_seats: int
    seats_used: int = 0
    seats_left: int = 0
    plan_domains: list[str] = Field(default_factory=list)
    contract_start: Optional[date] = None
    contract_end: Optional[date] = None
    created_at: Optional[datetime] = None


# ── bulk invite ──────────────────────────────────────────────────────────────
class BulkInviteRow(BaseModel):
    name: str = ""
    email: EmailStr


class BulkInviteRequest(BaseModel):
    """Parsed CSV rows (the router also accepts a raw CSV file upload)."""
    college_id: Optional[str] = None       # super admin must supply; college admin auto
    rows: list[BulkInviteRow] = Field(default_factory=list)


class InviteResult(BaseModel):
    email: str
    status: str                            # created | skipped_exists | skipped_no_seats | error
    temp_password: Optional[str] = None    # only for freshly created accounts


class BulkInviteResponse(BaseModel):
    college_id: str
    requested: int
    created: int
    skipped: int
    seats_left: int
    results: list[InviteResult]


# ── students ─────────────────────────────────────────────────────────────────
class StudentRow(BaseModel):
    id: str
    name: str = ""
    email: str = ""
    college_id: Optional[str] = None
    role: str = "student"
    profile_bar_score: Optional[int] = None
    created_at: Optional[datetime] = None


class StudentOverride(BaseModel):
    """Super-admin overrides; college admins get read-only student views."""
    name: Optional[str] = None
    college_id: Optional[str] = None
    reset_password: bool = False


class StudentOverrideResult(BaseModel):
    id: str
    updated_fields: list[str]
    temp_password: Optional[str] = None
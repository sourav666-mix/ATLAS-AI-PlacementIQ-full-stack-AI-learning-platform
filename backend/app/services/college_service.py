# college_service.py - bulk-invite logic + seat accounting
# backend/app/services/college_service.py
"""college_service — onboarding, seat accounting, CSV bulk-invite.

Seat model: a college buys license_seats; every student user whose
college_id points at the college consumes one seat. Bulk-invite creates
student accounts (with temp passwords) until the seats run out, then skips.

Role rules: super_admin manages any college; college_admin can only view
their own college + invite into it.
"""
from __future__ import annotations

import csv
import io
import secrets
import uuid

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.admin import (
    BulkInviteResponse,
    BulkInviteRow,
    CollegeCreate,
    CollegeRow,
    CollegeUpdate,
    InviteResult,
)
from app.services.admin_auth_service import hash_admin_password

# --- INTEGRATION POINT -------------------------------------------------------
from app.models.college import College      # Batch 2 model
from app.models.user import User            # Batch 1 model
# College expected: id, name, license_seats, plan_domains(JSON), contract_start,
#                   contract_end, created_at   (optional cols read defensively)
# -----------------------------------------------------------------------------


def _temp_password() -> str:
    return secrets.token_urlsafe(9)


async def _seats_used(db: AsyncSession, college_id: str) -> int:
    return (await db.execute(
        select(func.count(User.id)).where(User.college_id == college_id)
    )).scalar() or 0


def _row(college: College, used: int) -> CollegeRow:
    seats = int(getattr(college, "license_seats", 0) or 0)
    return CollegeRow(
        id=college.id,
        name=college.name or "",
        license_seats=seats,
        seats_used=used,
        seats_left=max(0, seats - used),
        plan_domains=list(getattr(college, "plan_domains", None) or []),
        contract_start=getattr(college, "contract_start", None),
        contract_end=getattr(college, "contract_end", None),
        created_at=getattr(college, "created_at", None),
    )


async def _get(db, college_id) -> College:
    row = (await db.execute(select(College).where(
        College.id == college_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(404, "College not found")
    return row


# ── CRUD ─────────────────────────────────────────────────────────────────────
async def create_college(db: AsyncSession, data: CollegeCreate) -> CollegeRow:
    row = College(id=str(uuid.uuid4()), name=data.name,
                  license_seats=data.license_seats)
    for col, val in (("plan_domains", data.plan_domains),
                     ("contract_start", data.contract_start),
                     ("contract_end", data.contract_end)):
        if hasattr(row, col):
            setattr(row, col, val)
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _row(row, 0)


async def update_college(db: AsyncSession, college_id: str,
                         data: CollegeUpdate) -> CollegeRow:
    row = await _get(db, college_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        if value is not None and hasattr(row, field):
            setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return _row(row, await _seats_used(db, college_id))


async def get_college(db: AsyncSession, college_id: str) -> CollegeRow:
    row = await _get(db, college_id)
    return _row(row, await _seats_used(db, college_id))


async def list_colleges(db: AsyncSession) -> list[CollegeRow]:
    rows = (await db.execute(select(College))).scalars().all()
    out = []
    for c in rows:
        out.append(_row(c, await _seats_used(db, c.id)))
    return out


# ── bulk invite ──────────────────────────────────────────────────────────────
def parse_invite_csv(raw: bytes) -> list[BulkInviteRow]:
    """Accepts 'name,email' or 'email' CSV (with or without a header row)."""
    text = raw.decode("utf-8-sig", errors="replace")
    rows: list[BulkInviteRow] = []
    for rec in csv.reader(io.StringIO(text)):
        cells = [c.strip() for c in rec if c.strip()]
        if not cells:
            continue
        email = next((c for c in cells if "@" in c), None)
        if not email or email.lower() in ("email", "e-mail"):
            continue  # header or malformed line
        name = next((c for c in cells if "@" not in c), "")
        try:
            rows.append(BulkInviteRow(name=name, email=email))
        except Exception:
            continue  # invalid email — skip the line, don't fail the batch
    return rows


async def bulk_invite(db: AsyncSession, college_id: str,
                      rows: list[BulkInviteRow]) -> BulkInviteResponse:
    college = await _get(db, college_id)
    seats = int(getattr(college, "license_seats", 0) or 0)
    used = await _seats_used(db, college_id)
    left = max(0, seats - used)

    results: list[InviteResult] = []
    created = skipped = 0
    for row in rows:
        email = row.email.strip().lower()
        exists = (await db.execute(select(User).where(
            User.email == email))).scalar_one_or_none()
        if exists:
            results.append(InviteResult(email=email, status="skipped_exists"))
            skipped += 1
            continue
        if left <= 0:
            results.append(InviteResult(email=email, status="skipped_no_seats"))
            skipped += 1
            continue
        temp = _temp_password()
        user = User(id=str(uuid.uuid4()), email=email)
        # optional columns, set only if present on the model
        for col, val in (("name", row.name), ("college_id", college_id),
                          ("password_hash", hash_admin_password(temp)),
                          ("role", "student")):
            if hasattr(user, col):
                setattr(user, col, val)
        db.add(user)
        results.append(InviteResult(email=email, status="created",
                                    temp_password=temp))
        created += 1
        left -= 1
    await db.commit()

    return BulkInviteResponse(
        college_id=college_id, requested=len(rows),
        created=created, skipped=skipped, seats_left=left, results=results,
    )
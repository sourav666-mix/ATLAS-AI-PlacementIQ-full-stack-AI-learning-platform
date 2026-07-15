# backend/app/services/jobs_admin_service.py
"""Jobs Board — posting + analytics service (admin / college-admin).

Role rules (v10 spec):
  * super_admin  : may post platform-wide (college_id NULL) or to a college.
  * college_admin: auto-scoped to their OWN college_id; may choose whether the
                   post is college_only or shared platform-wide (visibility).
There is NO public posting path — the router gate enforces the caller is staff.

`actor` is a small dict {id, role, college_id} produced by the router so this
service is decoupled from whichever auth layer supplies it.
"""
from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.jobs import (
    STAGES,
    AdminJobRow,
    JobPostCreate,
    JobPostUpdate,
    PostingAnalytics,
)

# --- INTEGRATION POINT ------------------------------------------------------
from app.models.job import JobPosting, JobTracking  # noqa: E402
# ---------------------------------------------------------------------------

SUPER_ROLES = {"super_admin", "admin"}
POSTER_ROLES = SUPER_ROLES | {"college_admin"}


def _require_poster(actor: dict) -> None:
    if actor.get("role") not in POSTER_ROLES:
        raise HTTPException(status_code=403, detail="Not permitted to post jobs")


def _resolve_college(actor: dict, requested: str | None) -> str | None:
    """super admin may target any college (or platform-wide); college admin is
    forced onto their own college."""
    if actor["role"] in SUPER_ROLES:
        return requested  # may be None => platform-wide
    return actor.get("college_id")  # college_admin: locked to own cohort


def _owns(actor: dict, posting: JobPosting) -> bool:
    if actor["role"] in SUPER_ROLES:
        return True
    return bool(actor.get("college_id")) and posting.college_id == actor["college_id"]


async def create_posting(db: AsyncSession, actor: dict, data: JobPostCreate) -> JobPosting:
    _require_poster(actor)
    if data.kind not in ("job", "internship"):
        raise HTTPException(status_code=400, detail="kind must be job|internship")

    visibility = data.visibility if data.visibility in ("all", "college_only") else "all"
    college_id = _resolve_college(actor, data.college_id)
    if actor["role"] == "college_admin" and not college_id:
        raise HTTPException(status_code=400, detail="College admin has no college_id")

    row = JobPosting(
        id=str(uuid.uuid4()),
        posted_by=actor["id"],
        college_id=college_id,
        visibility=visibility,
        kind=data.kind,
        title=data.title,
        company=data.company,
        location=data.location,
        work_mode=data.work_mode,
        ctc_band=data.ctc_band,
        stipend=data.stipend,
        required_skills_json=list(data.required_skills or []),
        eligibility_json=data.eligibility.model_dump() if data.eligibility else {},
        description=data.description,
        apply_url=data.apply_url,
        deadline=data.deadline,
        status="active",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def _get_owned(db, actor, job_id) -> JobPosting:
    row = (await db.execute(select(JobPosting).where(
        JobPosting.id == job_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    if not _owns(actor, row):
        raise HTTPException(status_code=403, detail="Not your posting")
    return row


async def update_posting(db, actor, job_id, data: JobPostUpdate) -> JobPosting:
    _require_poster(actor)
    row = await _get_owned(db, actor, job_id)
    patch = data.model_dump(exclude_unset=True)

    if "required_skills" in patch:
        row.required_skills_json = list(patch.pop("required_skills") or [])
    if "eligibility" in patch and patch["eligibility"] is not None:
        elig = patch.pop("eligibility")
        row.eligibility_json = elig if isinstance(elig, dict) else dict(elig)
    for field, value in patch.items():
        if value is not None and hasattr(row, field):
            setattr(row, field, value)
    await db.commit()
    await db.refresh(row)
    return row


async def expire_posting(db, actor, job_id) -> JobPosting:
    _require_poster(actor)
    row = await _get_owned(db, actor, job_id)
    row.status = "archived"
    await db.commit()
    await db.refresh(row)
    return row


def _scope(actor, stmt):
    """College admins only see their own postings."""
    if actor["role"] in SUPER_ROLES:
        return stmt
    return stmt.where(JobPosting.college_id == actor.get("college_id"))


async def _counts(db, job_id) -> tuple[int, int, dict[str, int]]:
    rows = (await db.execute(select(JobTracking).where(
        JobTracking.job_id == job_id))).scalars().all()
    by_stage = {s: 0 for s in STAGES}
    for r in rows:
        by_stage[r.stage] = by_stage.get(r.stage, 0) + 1
    saves = len(rows)
    applies = sum(by_stage.get(s, 0) for s in ("applied", "test", "interview", "offer"))
    return saves, applies, by_stage


async def list_postings(db, actor) -> list[AdminJobRow]:
    _require_poster(actor)
    stmt = _scope(actor, select(JobPosting)).order_by(JobPosting.created_at.desc())
    postings = (await db.execute(stmt)).scalars().all()
    out: list[AdminJobRow] = []
    for p in postings:
        saves, applies, _ = await _counts(db, p.id)
        out.append(AdminJobRow(
            id=p.id, kind=p.kind, title=p.title or "", company=p.company or "",
            visibility=p.visibility, college_id=p.college_id, status=p.status,
            deadline=getattr(p, "deadline", None), saves=saves, applies=applies,
            created_at=getattr(p, "created_at", None),
        ))
    return out


async def analytics(db, actor, job_id: str | None = None) -> list[PostingAnalytics]:
    _require_poster(actor)
    stmt = _scope(actor, select(JobPosting))
    if job_id:
        stmt = stmt.where(JobPosting.id == job_id)
    postings = (await db.execute(stmt)).scalars().all()
    out: list[PostingAnalytics] = []
    for p in postings:
        saves, applies, by_stage = await _counts(db, p.id)
        out.append(PostingAnalytics(job_id=p.id, title=p.title or "",
                                    saves=saves, applies=applies, by_stage=by_stage))
    return out
# jobs_service.py - [NEW] match score via stored embeddings (no live LLM)
# backend/app/services/jobs_service.py
"""Jobs Board — student read + tracking service (no LLM anywhere here).

Responsibilities:
  * list active postings the student is allowed to see (college scoping)
  * auto-archive postings past their deadline (lazy, on read)
  * attach a personal match score + tracked stage to each card
  * save / advance the application pipeline (saved -> ... -> offer)
  * build the tracker kanban
"""
from __future__ import annotations

import uuid
from datetime import date

from fastapi import HTTPException
from sqlalchemy import and_, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.jobs import (
    STAGES,
    Eligibility,
    JobCard,
    JobDetail,
    TrackerBoard,
    TrackerItem,
)
from app.services import (
    company_registry,      # Batch 11 — resolve company -> Intel slug for deep link
    job_match_service,
    student_skills_service,
)

# --- INTEGRATION POINT ------------------------------------------------------
# job.py models (Batch 3). Expected: JobPosting(job_postings), JobTracking(job_tracking).
from app.models.job import JobPosting, JobTracking  # noqa: E402
# ---------------------------------------------------------------------------

_COLLEGE_ATTRS = ("college_id", "college", "org_id")


def _student_college(user) -> str | None:
    for a in _COLLEGE_ATTRS:
        if hasattr(user, a):
            val = getattr(user, a)
            if val:
                return val
    return None


def _visibility_filter(user):
    college_id = _student_college(user)
    everyone = JobPosting.visibility == "all"
    if college_id:
        return or_(everyone, and_(JobPosting.visibility == "college_only",
                                  JobPosting.college_id == college_id))
    return everyone


def _skills_of(posting) -> list[str]:
    raw = getattr(posting, "required_skills_json", None) or []
    if isinstance(raw, dict):
        raw = raw.get("skills", []) or []
    return [str(s) for s in raw]


def _badge(posting) -> tuple[bool, str]:
    if getattr(posting, "college_id", None):
        return False, "Posted by Placement Cell"
    return True, "Verified by ATLAS AI"


def _prep_link(company: str) -> str | None:
    slug = company_registry.resolve_slug(company or "")
    return f"/company/{slug}" if slug else None


def _card(posting, match: int, tracked_stage: str | None) -> JobCard:
    verified, badge = _badge(posting)
    return JobCard(
        id=posting.id,
        kind=getattr(posting, "kind", "job"),
        title=posting.title or "",
        company=posting.company or "",
        location=getattr(posting, "location", "") or "",
        work_mode=getattr(posting, "work_mode", "") or "",
        ctc_band=getattr(posting, "ctc_band", "") or "",
        stipend=getattr(posting, "stipend", "") or "",
        deadline=getattr(posting, "deadline", None),
        posted_at=getattr(posting, "created_at", None),
        skills=_skills_of(posting),
        match_score=match,
        match_band=job_match_service.band(match),
        tracked_stage=tracked_stage,
        verified=verified,
        badge=badge,
        prep_link=_prep_link(posting.company or ""),
        tailor_resume_link=f"/resume/analyze?job_id={posting.id}",
    )


async def _archive_expired(db: AsyncSession) -> None:
    await db.execute(
        update(JobPosting)
        .where(JobPosting.status == "active", JobPosting.deadline < date.today())
        .values(status="archived")
    )
    await db.commit()


async def _tracking_map(db: AsyncSession, user_id, job_ids=None) -> dict[str, JobTracking]:
    stmt = select(JobTracking).where(JobTracking.user_id == user_id)
    if job_ids is not None:
        stmt = stmt.where(JobTracking.job_id.in_(list(job_ids)))
    rows = (await db.execute(stmt)).scalars().all()
    return {r.job_id: r for r in rows}


async def list_jobs(db, user, *, kind=None, q=None, min_match=0) -> list[JobCard]:
    await _archive_expired(db)

    stmt = select(JobPosting).where(
        JobPosting.status == "active", _visibility_filter(user)
    )
    if kind:
        stmt = stmt.where(JobPosting.kind == kind)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(JobPosting.title.ilike(like),
                              JobPosting.company.ilike(like)))
    postings = (await db.execute(stmt)).scalars().all()

    skills = await student_skills_service.get_student_skills(db, user.id)
    tracking = await _tracking_map(db, user.id, [p.id for p in postings])

    cards: list[JobCard] = []
    for p in postings:
        match = job_match_service.score(_skills_of(p), skills)
        if match < (min_match or 0):
            continue
        stage = tracking[p.id].stage if p.id in tracking else None
        cards.append(_card(p, match, stage))

    cards.sort(key=lambda c: (-c.match_score, c.deadline or date.max))
    return cards


async def _get_posting(db, job_id) -> JobPosting:
    row = (await db.execute(
        select(JobPosting).where(JobPosting.id == job_id))).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return row


async def get_detail(db, user, job_id) -> JobDetail:
    p = await _get_posting(db, job_id)
    skills = await student_skills_service.get_student_skills(db, user.id)
    match, _band, gap = job_match_service.evaluate(_skills_of(p), skills)
    tracking = await _tracking_map(db, user.id, [p.id])
    stage = tracking[p.id].stage if p.id in tracking else None

    card = _card(p, match, stage)
    elig_raw = getattr(p, "eligibility_json", None) or {}
    return JobDetail(
        **card.model_dump(),
        description=getattr(p, "description", "") or "",
        apply_url=getattr(p, "apply_url", "") or "",
        eligibility=Eligibility(**elig_raw) if isinstance(elig_raw, dict) else Eligibility(),
        gap=gap if match < job_match_service.GOOD_AT else [],
    )


async def save_job(db, user, job_id) -> JobDetail:
    p = await _get_posting(db, job_id)
    skills = await student_skills_service.get_student_skills(db, user.id)
    match = job_match_service.score(_skills_of(p), skills)

    existing = (await db.execute(select(JobTracking).where(
        JobTracking.user_id == user.id, JobTracking.job_id == job_id)
    )).scalar_one_or_none()
    if existing:
        existing.match_score = match          # refresh snapshot, keep current stage
    else:
        db.add(JobTracking(id=str(uuid.uuid4()), user_id=user.id, job_id=job_id,
                           stage="saved", match_score=match))
    await db.commit()
    return await get_detail(db, user, job_id)


async def update_stage(db, user, job_id, stage: str) -> TrackerItem:
    if stage not in STAGES:
        raise HTTPException(status_code=400,
                            detail=f"stage must be one of {STAGES}")
    p = await _get_posting(db, job_id)
    row = (await db.execute(select(JobTracking).where(
        JobTracking.user_id == user.id, JobTracking.job_id == job_id)
    )).scalar_one_or_none()
    if not row:
        skills = await student_skills_service.get_student_skills(db, user.id)
        row = JobTracking(id=str(uuid.uuid4()), user_id=user.id, job_id=job_id,
                          stage=stage,
                          match_score=job_match_service.score(_skills_of(p), skills))
        db.add(row)
    else:
        row.stage = stage
    await db.commit()
    await db.refresh(row)
    return TrackerItem(job_id=job_id, title=p.title or "", company=p.company or "",
                       stage=row.stage, match_score=row.match_score,
                       deadline=getattr(p, "deadline", None),
                       updated_at=getattr(row, "updated_at", None))


async def get_tracker(db, user) -> TrackerBoard:
    rows = (await db.execute(select(JobTracking).where(
        JobTracking.user_id == user.id))).scalars().all()
    by_id = {}
    if rows:
        postings = (await db.execute(select(JobPosting).where(
            JobPosting.id.in_([r.job_id for r in rows])))).scalars().all()
        by_id = {p.id: p for p in postings}

    columns: dict[str, list[TrackerItem]] = {s: [] for s in STAGES}
    for r in rows:
        p = by_id.get(r.job_id)
        columns.setdefault(r.stage, []).append(TrackerItem(
            job_id=r.job_id,
            title=(p.title if p else "") or "",
            company=(p.company if p else "") or "",
            stage=r.stage,
            match_score=r.match_score,
            deadline=getattr(p, "deadline", None) if p else None,
            updated_at=getattr(r, "updated_at", None),
        ))
    return TrackerBoard(columns=columns)
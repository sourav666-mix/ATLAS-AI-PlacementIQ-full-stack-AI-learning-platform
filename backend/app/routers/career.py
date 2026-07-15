"""
ATLAS AI v12 — Career Target & Gap Engine router.

TYPE A (zero AI):  GET /career/companies, POST /career/profile, GET /career/profile,
                   POST /career/resume-parse
TYPE B (one call): POST /career/analyze   <- cached by fingerprint
"""
from __future__ import annotations

import io
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.career_target import CareerGapReport, CareerProfile, CareerTarget
from app.schemas.career_target import (
    CareerProfileIn, CareerProfileOut, CompanyOut, GapReportOut, ResumeParseOut,
)
from app.services import company_benchmark_service as bench
from app.services import gap_engine_service as gapx
from app.services import profile_score_service as scorer
from app.services.career_plan_service import get_or_create_report
from app.dependencies import get_current_user

router = APIRouter(prefix="/career", tags=["Career Target"])

_KNOWN_SKILL_TOKENS = sorted({
    s for lst in scorer.DOMAIN_CORE.values() for s in lst
} | scorer.DEPLOY_SKILLS | scorer.LANGUAGES | scorer.DB_SKILLS)


def _uid(user: Any) -> str:
    return str(getattr(user, "id", None) or (user.get("id") if isinstance(user, dict) else ""))


async def _load_profile(db: AsyncSession, user_id: str) -> CareerProfile | None:
    res = await db.execute(select(CareerProfile).where(CareerProfile.user_id == user_id))
    return res.scalar_one_or_none()


def _profile_to_dict(p: CareerProfile) -> Dict[str, Any]:
    return {
        "full_name": p.full_name, "branch": p.branch, "specialization": p.specialization,
        "target_domain": p.target_domain,
        "leetcode_easy": p.leetcode_easy or 0,
        "leetcode_medium": p.leetcode_medium or 0,
        "leetcode_hard": p.leetcode_hard or 0,
        "sql_level": p.sql_level, "sql_details": p.sql_details,
        "skills": p.skills_json or [], "projects": p.projects_json or [],
        "internships": p.internships_json or [],
        "certifications": p.certifications_json or [],
        "resume_text": p.resume_text,
        "github_url": p.github_url, "linkedin_url": p.linkedin_url,
        "aptitude_self": p.aptitude_self, "communication_self": p.communication_self,
    }


async def _platform_signals(db: AsyncSession, user_id: str) -> Dict[str, int]:
    """
    Real evidence from the rest of ATLAS. Every lookup is optional — if a table
    isn't wired yet the signal is simply 0 and the score falls back to self-report
    (which is capped at 60). Never raises.
    """
    sig: Dict[str, int] = {}
    try:
        from app.models.arena import ArenaSubmission  # type: ignore
        from sqlalchemy import func
        r = await db.execute(
            select(func.count(func.distinct(ArenaSubmission.problem_id)))
            .where(ArenaSubmission.user_id == user_id, ArenaSubmission.passed == 1)
        )
        sig["arena_solved"] = int(r.scalar() or 0)
    except Exception:
        pass
    try:
        from app.models.skill_progress import UserTopicProgress  # type: ignore
        from sqlalchemy import func
        r = await db.execute(
            select(func.avg(UserTopicProgress.mastery_score))
            .where(UserTopicProgress.user_id == user_id)
        )
        sig["skillpath_mastery_avg"] = int(r.scalar() or 0)
    except Exception:
        pass
    try:
        from app.models.career_target import CareerGapReport  # noqa: F401
        from app.models.session import MockSession  # type: ignore  # noqa: F401
    except Exception:
        pass
    return sig


# ------------------------------------------------------------------ Type A
@router.get("/companies", response_model=List[CompanyOut])
async def companies(domain: str, db: AsyncSession = Depends(get_db),
                    user=Depends(get_current_user)):
    """Pick-list of target companies for a domain. Pure DB read."""
    rows = await bench.list_companies(db, domain)
    if not rows:
        raise HTTPException(404, f"No benchmarks seeded for domain '{domain}'. "
                                 f"Run scripts/seed_company_benchmarks.py")
    return rows


@router.post("/profile", response_model=CareerProfileOut)
async def save_profile(payload: CareerProfileIn, db: AsyncSession = Depends(get_db),
                       user=Depends(get_current_user)):
    """
    Upsert the student's profile + up to 3 target companies.
    Computes profile score and every company gap. ZERO AI CALLS.
    """
    user_id = _uid(user)
    if not payload.targets:
        raise HTTPException(400, "Choose at least 1 target company (max 3).")
    if len(payload.targets) > 3:
        raise HTTPException(400, "Maximum 3 target companies.")

    data = payload.model_dump()
    pillars = scorer.compute_pillars(data, await _platform_signals(db, user_id))
    score = scorer.compute_profile_score(pillars)
    slugs = [t.company_slug for t in payload.targets]
    fp = scorer.fingerprint(data, slugs, pillars, bench.BENCHMARK_VERSION)

    profile = await _load_profile(db, user_id)
    if profile is None:
        profile = CareerProfile(user_id=user_id)
        db.add(profile)

    profile.full_name = payload.full_name
    profile.degree = payload.degree
    profile.branch = payload.branch
    profile.specialization = payload.specialization
    profile.college = payload.college
    profile.graduation_year = payload.graduation_year
    profile.cgpa = payload.cgpa
    profile.target_domain = payload.target_domain
    profile.leetcode_username = payload.leetcode_username
    profile.leetcode_easy = payload.leetcode_easy
    profile.leetcode_medium = payload.leetcode_medium
    profile.leetcode_hard = payload.leetcode_hard
    profile.github_url = payload.github_url
    profile.linkedin_url = payload.linkedin_url
    profile.sql_level = payload.sql_level
    profile.sql_details = payload.sql_details
    profile.skills_json = [s.model_dump() for s in payload.skills]
    profile.projects_json = [p.model_dump() for p in payload.projects]
    profile.internships_json = [i.model_dump() for i in payload.internships]
    profile.certifications_json = [c.model_dump() for c in payload.certifications]
    profile.resume_filename = payload.resume_filename
    profile.resume_text = payload.resume_text
    profile.aptitude_self = payload.aptitude_self
    profile.communication_self = payload.communication_self
    profile.profile_score = score
    profile.pillars_json = pillars
    profile.fingerprint = fp

    await db.flush()   # profile.id is now available

    # replace targets
    old = await db.execute(select(CareerTarget).where(CareerTarget.profile_id == profile.id))
    for row in old.scalars().all():
        await db.delete(row)
    await db.flush()

    benchmarks = await bench.get_benchmarks(db, slugs, payload.target_domain)
    priorities = {t.company_slug: t.priority for t in payload.targets}
    gaps = gapx.compute_all_gaps(pillars, benchmarks, priorities)

    for g in gaps:
        db.add(CareerTarget(
            profile_id=profile.id,
            company_slug=g["company_slug"],
            company_name=g["company_name"],
            priority=g["priority"],
            readiness_pct=g["readiness_pct"],
            gap_pct=g["gap_pct"],
            pillar_gaps_json=g["pillar_gaps"],
        ))

    await db.commit()

    cached = await db.execute(
        select(CareerGapReport.id).where(
            CareerGapReport.user_id == user_id, CareerGapReport.fingerprint == fp)
    )
    return {
        "profile_id": profile.id,
        "target_domain": payload.target_domain,
        "profile_score": score,
        "profile_grade": scorer.profile_grade(score),
        "pillars": pillars,
        "pillar_labels": scorer.PILLAR_LABELS,
        "fingerprint": fp,
        "targets": gaps,
        "has_cached_report": cached.scalar_one_or_none() is not None,
    }


@router.get("/profile", response_model=CareerProfileOut)
async def read_profile(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    user_id = _uid(user)
    profile = await _load_profile(db, user_id)
    if profile is None:
        raise HTTPException(404, "No career profile yet. POST /career/profile first.")

    pillars = profile.pillars_json or {}
    slugs = [t.company_slug for t in profile.targets]
    priorities = {t.company_slug: t.priority for t in profile.targets}
    benchmarks = await bench.get_benchmarks(db, slugs, profile.target_domain)
    gaps = gapx.compute_all_gaps(pillars, benchmarks, priorities)

    cached = await db.execute(
        select(CareerGapReport.id).where(
            CareerGapReport.user_id == user_id,
            CareerGapReport.fingerprint == profile.fingerprint)
    )
    return {
        "profile_id": profile.id,
        "target_domain": profile.target_domain,
        "profile_score": int(profile.profile_score or 0),
        "profile_grade": scorer.profile_grade(int(profile.profile_score or 0)),
        "pillars": pillars,
        "pillar_labels": scorer.PILLAR_LABELS,
        "fingerprint": profile.fingerprint or "",
        "targets": gaps,
        "has_cached_report": cached.scalar_one_or_none() is not None,
    }


@router.post("/resume-parse", response_model=ResumeParseOut)
async def resume_parse(file: UploadFile = File(...), user=Depends(get_current_user)):
    """Extract raw text from an uploaded PDF/DOCX/TXT. NO AI — pure parsing."""
    raw = await file.read()
    if len(raw) > 4 * 1024 * 1024:
        raise HTTPException(413, "Resume must be under 4 MB.")

    name = (file.filename or "").lower()
    text = ""
    try:
        if name.endswith(".pdf"):
            try:
                from pypdf import PdfReader           # pypdf >= 3
            except ImportError:
                from PyPDF2 import PdfReader          # legacy fallback
            reader = PdfReader(io.BytesIO(raw))
            text = "\n".join((pg.extract_text() or "") for pg in reader.pages)
        elif name.endswith(".docx"):
            import docx                               # python-docx
            d = docx.Document(io.BytesIO(raw))
            text = "\n".join(p.text for p in d.paragraphs)
        else:
            text = raw.decode("utf-8", errors="ignore")
    except Exception as exc:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Could not read that file ({exc.__class__.__name__}). "
            f"Upload a text-based PDF, DOCX or TXT.",
        )

    low = text.lower()
    detected = [t for t in _KNOWN_SKILL_TOKENS if t in low]

    links: Dict[str, str] = {}
    for token, key in (("github.com/", "github"), ("linkedin.com/in/", "linkedin"),
                       ("leetcode.com/", "leetcode")):
        i = low.find(token)
        if i != -1:
            tail = text[i:i + 90].split()[0].strip().rstrip(".,);|")
            links[key] = tail if tail.startswith("http") else "https://" + tail

    return {
        "resume_text": text[:20000],
        "detected_skills": detected[:40],
        "detected_links": links,
        "char_count": len(text),
    }


# ------------------------------------------------------------------ Type B
@router.post("/analyze", response_model=GapReportOut)
async def analyze(force: bool = False, db: AsyncSession = Depends(get_db),
                  user=Depends(get_current_user)):
    """
    The ONE bounded AI call. Cached by fingerprint — re-running with an unchanged
    profile costs nothing. `force=true` regenerates (admin/debug only).
    """
    user_id = _uid(user)
    profile = await _load_profile(db, user_id)
    if profile is None:
        raise HTTPException(404, "No career profile yet. POST /career/profile first.")
    if not profile.targets:
        raise HTTPException(400, "No target companies selected.")

    pillars = profile.pillars_json or {}
    slugs = [t.company_slug for t in profile.targets]
    priorities = {t.company_slug: t.priority for t in profile.targets}
    benchmarks = await bench.get_benchmarks(db, slugs, profile.target_domain)
    gaps = gapx.compute_all_gaps(pillars, benchmarks, priorities)

    report = await get_or_create_report(
        db,
        user_id=user_id,
        profile_id=profile.id,
        fingerprint=profile.fingerprint or "",
        profile=_profile_to_dict(profile),
        pillars=pillars,
        gaps=gaps,
        force=force,
    )
    report["profile_score"] = int(profile.profile_score or 0)
    return report


@router.get("/report", response_model=GapReportOut)
async def latest_report(db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    """Read the cached report only. NEVER triggers an AI call."""
    user_id = _uid(user)
    res = await db.execute(
        select(CareerGapReport)
        .where(CareerGapReport.user_id == user_id)
        .order_by(CareerGapReport.created_at.desc())
        .limit(1)
    )
    row = res.scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "No report yet. POST /career/analyze once.")
    body = dict(row.report_json or {})
    body["fingerprint"] = row.fingerprint
    body["source"] = "cache"
    body["generated_at"] = row.created_at.isoformat() if row.created_at else None
    body.setdefault("profile_score", 0)
    return body
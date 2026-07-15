# backend/app/services/student_skills_service.py
"""Assemble the student's skill picture: {normalized_skill: score 0-100}.

Single source of truth for "what does this student know", reused by the Jobs
Board match score. Primary signal is the live skill radar (Batch 11). Resume
skills are merged in as an optional bonus and are read *defensively* — a
missing/renamed resume model must never break job matching.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.gap_map_service import get_radar  # Batch 11 — reads skill_radar_scores
from app.utils.skill_match import normalize_skill

# score assigned to a skill that appears on the resume but not on the radar
RESUME_BASELINE = 70


def _extract_skill_strings(blob) -> set[str]:
    """Pull skill-ish strings out of a resume_json / analysis_json blob."""
    found: set[str] = set()
    if not blob:
        return found
    if isinstance(blob, str):
        return found
    if isinstance(blob, list):
        for item in blob:
            found |= _extract_skill_strings(item)
        return found
    if isinstance(blob, dict):
        for key in ("skills", "skill_list", "technical_skills", "matched_skills",
                    "key_skills", "hard_skills"):
            val = blob.get(key)
            if isinstance(val, list):
                found |= {str(v) for v in val if isinstance(v, (str, int, float))}
            elif isinstance(val, str):
                found |= {p.strip() for p in val.replace(";", ",").split(",") if p.strip()}
    return found


async def _resume_skills(db: AsyncSession, user_id) -> set[str]:
    """Latest resume's skills, normalized. Lazy import so a schema mismatch
    degrades gracefully instead of crashing the whole match path."""
    try:
        from sqlalchemy import select
        from app.models.resume_doc import ResumeDocument  # Batch 10 model
    except Exception:
        return set()
    try:
        stmt = (
            select(ResumeDocument)
            .where(ResumeDocument.user_id == user_id)
            .order_by(ResumeDocument.created_at.desc())
            .limit(1)
        )
        row = (await db.execute(stmt)).scalars().first()
    except Exception:
        return set()
    if not row:
        return set()
    raw: set[str] = set()
    for attr in ("resume_json", "analysis_json"):
        raw |= _extract_skill_strings(getattr(row, attr, None))
    return {normalize_skill(s) for s in raw if normalize_skill(s)}


async def get_student_skills(db: AsyncSession, user_id) -> dict[str, int]:
    skills: dict[str, int] = dict(await get_radar(db, user_id))
    for norm in await _resume_skills(db, user_id):
        skills.setdefault(norm, RESUME_BASELINE)
    return skills
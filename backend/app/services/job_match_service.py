# backend/app/services/job_match_service.py
"""Smart Match Score — pure NLP over stored skill data, ZERO live LLM.

match_score(0-100) = how much of a posting's required skills the student covers,
weighted by their radar mastery. Below 60% we surface a 'Close the gap' list
pointing at the exact SkillPath topics (reusing Batch 11's skillpath_links).
"""
from __future__ import annotations

from app.schemas.jobs import GapSkill
from app.services import skillpath_links
from app.utils.skill_match import normalize_skill, to_skill_map

GREAT_AT = 75
GOOD_AT = 60
# a required skill is "covered" once the student's mastery reaches this
COVERED_AT = 60


def band(match: int) -> str:
    if match >= GREAT_AT:
        return "great"
    if match >= GOOD_AT:
        return "good"
    return "stretch"


def score(required_skills, student_skills: dict[str, int]) -> int:
    """Mean mastery (0-100) across the posting's required skills."""
    req = to_skill_map(required_skills)  # {normalized: original_label}
    if not req:
        return 0
    total = 0
    for norm in req:
        s = student_skills.get(norm, 0)
        total += max(0, min(int(s or 0), 100))
    return round(total / (100 * len(req)) * 100)


def gap(required_skills, student_skills: dict[str, int]) -> list[GapSkill]:
    """Skills the student should close for this posting (below covered)."""
    req = to_skill_map(required_skills)
    out: list[GapSkill] = []
    for norm, label in req.items():
        s = student_skills.get(norm)
        cur = int(s) if s is not None else None
        if cur is None or cur < COVERED_AT:
            out.append(GapSkill(
                skill=label,
                radar_score=cur,
                fix_topic=skillpath_links.topic_for(label),
                fix_link=skillpath_links.link_for(label),
            ))
    # neediest first (missing before low-mastery)
    out.sort(key=lambda g: (g.radar_score if g.radar_score is not None else -1))
    return out


def evaluate(required_skills, student_skills: dict[str, int]) -> tuple[int, str, list[GapSkill]]:
    m = score(required_skills, student_skills)
    return m, band(m), gap(required_skills, student_skills)
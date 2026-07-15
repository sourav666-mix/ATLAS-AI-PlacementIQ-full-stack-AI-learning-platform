# backend/app/services/gap_map_service.py
"""Personal skill-gap map + company compare — pure SQL + set math, ZERO AI.

Gap map = company.required_skills vs the student's skill_radar_scores.
This is the feature no competitor has, precisely because it reads the student's
own live radar. It must never call an LLM (System Understanding, section 11).
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.company import (
    CompareResponse,
    CompareRow,
    GapItem,
    GapMapResponse,
)
from app.services import skillpath_links
from app.utils.skill_match import normalize_skill

# --- INTEGRATION POINT ------------------------------------------------------
# The skill_radar_scores model. Table columns are read defensively below so a
# small naming difference in your model won't break this. Adjust the import if
# your class lives elsewhere.
from app.models.skill_progress import SkillRadarScore  # noqa: E402

# candidate attribute names on a radar row (first hit wins)
_CATEGORY_ATTRS = ("category", "skill_category", "skill", "spoke", "name", "label")
_SCORE_ATTRS = ("score", "mastery_score", "value", "radar_score", "pct", "percent")
_USER_ATTRS = ("user_id", "student_id", "owner_id")
# ---------------------------------------------------------------------------

READY_AT = 70
PRACTICE_AT = 40


def _first_attr(obj, names, default=None):
    for n in names:
        if hasattr(obj, n):
            return getattr(obj, n)
    return default


async def get_radar(db: AsyncSession, user_id) -> dict[str, int]:
    """Return {normalized_skill: score(0-100)} for the student."""
    user_col = None
    for n in _USER_ATTRS:
        if hasattr(SkillRadarScore, n):
            user_col = getattr(SkillRadarScore, n)
            break
    stmt = select(SkillRadarScore)
    if user_col is not None:
        stmt = stmt.where(user_col == user_id)
    rows = (await db.execute(stmt)).scalars().all()

    radar: dict[str, int] = {}
    for row in rows:
        cat = _first_attr(row, _CATEGORY_ATTRS, "")
        raw_score = _first_attr(row, _SCORE_ATTRS, 0)
        if not cat:
            continue
        try:
            score = int(round(float(raw_score or 0)))
        except (TypeError, ValueError):
            score = 0
        radar[normalize_skill(str(cat))] = score
    return radar


def build_gap_map(company: dict, report: dict, radar: dict[str, int]) -> GapMapResponse:
    required = report.get("required_skills") or []
    seen: set[str] = set()
    items: list[GapItem] = []
    ready = practice = missing = 0

    for raw in required:
        label = str(raw).strip()
        norm = normalize_skill(label)
        if not norm or norm in seen:
            continue
        seen.add(norm)

        score = radar.get(norm)
        if score is None:
            status, missing = "missing", missing + 1
        elif score >= READY_AT:
            status, ready = "ready", ready + 1
        elif score >= PRACTICE_AT:
            status, practice = "practice", practice + 1
        else:
            status, missing = "missing", missing + 1

        item = GapItem(skill=label, status=status, radar_score=score)
        if status != "ready":
            item.fix_topic = skillpath_links.topic_for(label)
            item.fix_link = skillpath_links.link_for(label)
        items.append(item)

    total = ready + practice + missing
    pct = round((ready + 0.5 * practice) / total * 100) if total else 0
    # green first, then amber, then red — matches the UI colour order
    order = {"ready": 0, "practice": 1, "missing": 2}
    items.sort(key=lambda i: order.get(i.status, 3))

    return GapMapResponse(
        company_slug=company["slug"],
        company_name=company["name"],
        readiness_pct=pct,
        counts={"ready": ready, "practice": practice, "missing": missing},
        items=items,
    )


def _pkg(report: dict, key: str) -> str:
    pkg = report.get("packages") or {}
    if isinstance(pkg, dict):
        return str(pkg.get(key, "") or "")
    return ""


def compare(company_a: dict, report_a: dict,
            company_b: dict, report_b: dict) -> CompareResponse:
    def row(metric, va, vb):
        return CompareRow(metric=metric, a=str(va or "—"), b=str(vb or "—"))

    hp_a = report_a.get("hiring_pattern") or {}
    hp_b = report_b.get("hiring_pattern") or {}
    rows = [
        row("Sector", company_a["sector"], company_b["sector"]),
        row("Average package", _pkg(report_a, "average"), _pkg(report_b, "average")),
        row("Highest package", _pkg(report_a, "highest"), _pkg(report_b, "highest")),
        row("CGPA cutoff", hp_a.get("cgpa_cutoff"), hp_b.get("cgpa_cutoff")),
        row("Coding platform", hp_a.get("coding_platform"), hp_b.get("coding_platform")),
        row("Interview rounds",
            len(report_a.get("interview_process") or []),
            len(report_b.get("interview_process") or [])),
        row("Required skills",
            len(report_a.get("required_skills") or []),
            len(report_b.get("required_skills") or [])),
    ]
    return CompareResponse(
        a_slug=company_a["slug"], b_slug=company_b["slug"],
        a_name=company_a["name"], b_name=company_b["name"],
        rows=rows,
    )
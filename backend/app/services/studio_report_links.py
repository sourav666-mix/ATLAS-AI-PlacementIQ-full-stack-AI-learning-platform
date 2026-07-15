# backend/app/services/studio_report_links.py
"""Map interview weaknesses to REAL ATLAS AI features — the improvement plan.

Pure string logic, no AI, no DB. The spec requires the final report's plan to
link to actual platform features ("DP weak → DSA Gym: Dynamic Programming"),
not generic advice. Reuses skill normalization from Batch 11.
"""
from __future__ import annotations

from urllib.parse import quote

from app.schemas.studio import PlatformPlanItem
from app.utils.skill_match import normalize_skill

# normalized weakness keyword -> (feature name, route builder)
_FEATURE_MAP: list[tuple[tuple[str, ...], str, str]] = [
    # (match keywords)                          feature name        route
    (("dynamic programming", "dp", "recursion", "graphs", "trees", "arrays",
      "linked list", "data structures", "algorithms", "sorting", "searching"),
     "DSA Gym", "/dsa?topic={q}"),
    (("sql", "databases", "joins", "indexing", "queries", "normalization"),
     "Code Arena — SQL", "/arena?category=sql&topic={q}"),
    (("coding", "python", "java", "c++", "implementation", "syntax"),
     "Code Arena", "/arena?topic={q}"),
    (("system design", "scalability", "architecture", "caching",
      "load balancing"),
     "SkillPath — System Design", "/skillpath/search?q={q}"),
    (("machine learning", "deep learning", "statistics", "probability",
      "model evaluation", "ml"),
     "SkillPath", "/skillpath/search?q={q}"),
    (("aptitude", "quantitative", "logic", "reasoning"),
     "Assessment Center — Aptitude", "/assessment?tab=aptitude&topic={q}"),
    (("communication", "clarity", "articulation", "confidence", "star",
      "behavioral", "hr"),
     "Assessment Center — Mock Interview", "/assessment?tab=interview"),
    (("resume", "projects", "portfolio"),
     "Resume AI 2.0", "/resume"),
]

_DEFAULT_FEATURE = ("SkillPath", "/skillpath/search?q={q}")


def _match(weakness_norm: str) -> tuple[str, str]:
    for keywords, feature, route in _FEATURE_MAP:
        for kw in keywords:
            if kw in weakness_norm or weakness_norm in kw:
                return feature, route
    return _DEFAULT_FEATURE


def build_plan(weaknesses: list[str]) -> list[PlatformPlanItem]:
    """One actionable platform link per distinct weakness."""
    seen: set[str] = set()
    plan: list[PlatformPlanItem] = []
    for raw in weaknesses or []:
        label = str(raw).strip()
        norm = normalize_skill(label)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        feature, route = _match(norm)
        plan.append(PlatformPlanItem(
            weakness=label,
            feature=feature,
            link=route.format(q=quote(label)),
            why=f"Targeted practice for '{label}' inside {feature}.",
        ))
    return plan
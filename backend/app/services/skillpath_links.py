# backend/app/services/skillpath_links.py
"""Map a required skill to a SkillPath deep-link + a best-guess topic label.

Pure string logic (no DB) so the gap map can hand each red/amber skill a
"go fix this" link without a fragile join against roadmap_topics. The frontend
resolves /skillpath/search?q=... to the real topic card. If you later want an
exact topic id, swap `topic_for()` for a roadmap_topics lookup — the router
contract does not change.
"""
from __future__ import annotations

from urllib.parse import quote

from app.utils.skill_match import normalize_skill

# Optional: nudge a few skills straight to a named topic instead of search.
_TOPIC_HINTS: dict[str, str] = {
    "data structures": "Data Structures & Algorithms",
    "algorithms": "Data Structures & Algorithms",
    "sql": "SQL & Databases",
    "databases": "SQL & Databases",
    "python": "Python",
    "java": "Java",
    "javascript": "JavaScript",
    "machine learning": "Machine Learning Foundations",
    "deep learning": "Deep Learning",
    "system design": "System Design",
    "oop": "OOP Concepts",
    "rest": "APIs & REST",
    "aptitude": "Quantitative Aptitude",
}


def topic_for(skill: str) -> str:
    norm = normalize_skill(skill)
    return _TOPIC_HINTS.get(norm, skill.strip().title())


def link_for(skill: str) -> str:
    """Frontend route the 'Close the gap' button points at."""
    return f"/skillpath/search?q={quote(skill.strip())}"
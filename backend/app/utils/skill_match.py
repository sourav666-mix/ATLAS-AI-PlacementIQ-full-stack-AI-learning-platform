# backend/app/utils/skill_match.py
"""Pure skill-name normalization + set math.

Used by the Company Intel gap map (company required_skills vs the student's
skill_radar_scores). No LLM, no DB — this is deliberately dumb string logic so
the gap map stays a "pure SQL + set math" feature per the v10 spec.
"""
from __future__ import annotations

import re

# Common aliases → canonical token. Extend freely; it only helps matching.
_ALIASES: dict[str, str] = {
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "golang": "go",
    "reactjs": "react",
    "react.js": "react",
    "nodejs": "node",
    "node.js": "node",
    "postgres": "postgresql",
    "postgre": "postgresql",
    "ml": "machine learning",
    "dl": "deep learning",
    "ds": "data structures",
    "dsa": "data structures",
    "oops": "oop",
    "restapi": "rest",
    "restful": "rest",
    "k8s": "kubernetes",
    "tf": "tensorflow",
    "cv": "computer vision",
    "nlp": "natural language processing",
    "db": "databases",
    "sql server": "sql",
    "mysql": "sql",
    "dbms": "databases",
}

_PUNCT = re.compile(r"[^a-z0-9+#. ]+")
_SPACE = re.compile(r"\s+")


def normalize_skill(raw: str) -> str:
    """Lowercase, strip noise, collapse spaces, apply aliases."""
    if not raw:
        return ""
    s = raw.strip().lower()
    s = _PUNCT.sub(" ", s)
    s = _SPACE.sub(" ", s).strip()
    return _ALIASES.get(s, s)


def to_skill_map(names) -> dict[str, str]:
    """Map normalized -> original label (keeps a human-readable version)."""
    out: dict[str, str] = {}
    for n in names or []:
        norm = normalize_skill(str(n))
        if norm and norm not in out:
            out[norm] = str(n).strip()
    return out


def to_skill_set(names) -> set[str]:
    return set(to_skill_map(names).keys())


def coverage(required, have) -> tuple[set[str], set[str]]:
    """Return (matched, missing) normalized skill sets."""
    req = to_skill_set(required)
    hv = to_skill_set(have)
    matched = req & hv
    missing = req - hv
    return matched, missing


def readiness_pct(required, have_scores: dict[str, int],
                  ready_at: int = 70, practice_at: int = 40) -> int:
    """0-100 readiness: full credit for ready skills, half for in-progress."""
    req = to_skill_set(required)
    if not req:
        return 0
    ready = practice = 0
    for skill in req:
        score = have_scores.get(skill)
        if score is None:
            continue
        if score >= ready_at:
            ready += 1
        elif score >= practice_at:
            practice += 1
    return round((ready + 0.5 * practice) / len(req) * 100)
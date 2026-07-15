"""
ATLAS AI v12 — Profile Score (PURE MATH, ZERO AI).

Nine pillars. Every pillar is 0-100. Self-reported skills are EVIDENCE-DAMPED:
a claim with no project / no LeetCode / no platform signal behind it is capped
at 60, so the score cannot be inflated by ticking boxes.

Import anywhere. No DB, no network, no AI. Unit-testable in isolation.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------- taxonomy
PILLARS: List[str] = [
    "programming",
    "dsa",
    "database_sql",
    "core_domain",
    "projects",
    "deployment",
    "aptitude",
    "communication",
    "resume_ats",
]

PILLAR_LABELS: Dict[str, str] = {
    "programming": "Programming Fluency",
    "dsa": "DSA & Problem Solving",
    "database_sql": "Databases / SQL",
    "core_domain": "Core Domain Depth",
    "projects": "Project Portfolio",
    "deployment": "Deployment & Git",
    "aptitude": "Aptitude & Reasoning",
    "communication": "Communication / Interview",
    "resume_ats": "Resume & ATS",
}

LABEL_SCORE: Dict[str, int] = {
    "beginner": 20,
    "learning": 40,
    "comfortable": 60,
    "strong": 80,
    "expert": 95,
}

SQL_LEVEL_SCORE: Dict[str, int] = {
    "none": 5,
    "basic": 35,
    "intermediate": 65,
    "advanced": 88,
}

# Cap applied to any self-claim with zero corroborating evidence.
UNEVIDENCED_CAP = 60

# Domain core skill lists — what "core_domain" actually means per track.
DOMAIN_CORE: Dict[str, List[str]] = {
    "data_science": ["python", "pandas", "numpy", "statistics", "machine learning",
                     "sql", "matplotlib", "scikit-learn"],
    "data_analysis": ["excel", "sql", "power bi", "tableau", "pandas",
                      "statistics", "data cleaning"],
    "artificial_intelligence": ["python", "machine learning", "deep learning",
                                "pytorch", "tensorflow", "linear algebra", "nlp"],
    "generative_ai": ["python", "llm", "prompt engineering", "rag", "langchain",
                      "embeddings", "vector database", "transformers"],
    "frontend": ["html", "css", "javascript", "react", "typescript",
                 "tailwind", "responsive design", "state management"],
    "backend": ["python", "java", "rest api", "sql", "fastapi", "spring",
                "authentication", "system design"],
    "cloud": ["linux", "aws", "docker", "kubernetes", "networking",
              "terraform", "ci/cd"],
    "mlops": ["python", "docker", "kubernetes", "mlflow", "ci/cd",
              "monitoring", "model serving", "aws"],
    "cybersecurity": ["linux", "networking", "cryptography", "owasp",
                      "wireshark", "penetration testing", "python"],
}

DEPLOY_SKILLS = {"git", "github", "docker", "aws", "azure", "gcp", "heroku",
                 "render", "vercel", "netlify", "kubernetes", "ci/cd", "linux",
                 "nginx", "streamlit"}

LANGUAGES = {"python", "java", "c++", "cpp", "c", "javascript", "typescript",
             "go", "rust", "kotlin", "c#", "sql", "r"}

DB_SKILLS = {"sql", "mysql", "postgresql", "postgres", "mongodb", "sqlite",
             "oracle", "redis"}


# ---------------------------------------------------------------- helpers
def _norm(s: Any) -> str:
    return str(s or "").strip().lower()


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> int:
    return int(round(max(lo, min(hi, v))))


def _skill_map(skills: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for s in skills or []:
        name = _norm(s.get("name"))
        if not name:
            continue
        out[name] = s
    return out


def _evidence_terms(projects: List[Dict[str, Any]],
                    internships: List[Dict[str, Any]],
                    profile: Dict[str, Any]) -> set:
    """Every lowercase token that counts as *proof* a skill was actually used."""
    terms: set = set()
    for p in projects or []:
        for t in p.get("tech") or []:
            terms.add(_norm(t))
        terms.update(_norm(p.get("description")).split())
        terms.update(_norm(p.get("title")).split())
    for i in internships or []:
        terms.update(_norm(i.get("work")).split())
        terms.update(_norm(i.get("role")).split())
    terms.update(_norm(profile.get("sql_details")).split())
    terms.update(_norm(profile.get("resume_text")).split())
    return terms


def _rated(skill: Dict[str, Any] | None, evidence: set,
           platform_boost: int = 0) -> int:
    """Score one skill: label -> number, damped unless proven, then boosted by platform data."""
    if not skill:
        return 0 + platform_boost
    base = LABEL_SCORE.get(_norm(skill.get("label")), 40)
    name = _norm(skill.get("name"))
    proven = (
        bool(skill.get("evidence"))
        or name in evidence
        or any(name and name in t for t in evidence)
    )
    if not proven:
        base = min(base, UNEVIDENCED_CAP)
    return _clamp(base + platform_boost)


# ---------------------------------------------------------------- pillars
def score_dsa(easy: int, medium: int, hard: int, arena_solved: int = 0) -> int:
    """
    Weighted LeetCode volume. 1 / 2.5 / 5 points. ~450 weighted points = 100.
    Arena problems solved on ATLAS count the same as a Medium.
    """
    raw = (max(0, easy) * 1.0
           + max(0, medium) * 2.5
           + max(0, hard) * 5.0
           + max(0, arena_solved) * 2.5)
    return _clamp(raw / 4.5)


def score_programming(smap: Dict[str, Dict], evidence: set, signals: Dict) -> int:
    langs = [_rated(smap[n], evidence) for n in smap if n in LANGUAGES and n != "sql"]
    if not langs:
        return _clamp(signals.get("lab_completions", 0) * 3)
    langs.sort(reverse=True)
    best = langs[0]
    breadth = min(15, 5 * (len(langs) - 1))          # 2nd/3rd language = small bonus
    lab_boost = min(12, signals.get("lab_completions", 0) * 2)
    return _clamp(best * 0.85 + breadth + lab_boost)


def score_database_sql(profile: Dict, smap: Dict, evidence: set, signals: Dict) -> int:
    declared = SQL_LEVEL_SCORE.get(_norm(profile.get("sql_level")), 5)
    skill = max((_rated(smap[n], evidence) for n in smap if n in DB_SKILLS), default=0)
    detail_depth = 0
    d = _norm(profile.get("sql_details"))
    for kw, pts in (("join", 6), ("group by", 5), ("window", 10), ("subquery", 6),
                    ("index", 6), ("cte", 6), ("normal", 4), ("transaction", 5)):
        if kw in d:
            detail_depth += pts
    detail_depth = min(25, detail_depth)
    lab_boost = min(10, signals.get("sql_lab_completions", 0) * 3)
    return _clamp(0.55 * declared + 0.30 * skill + detail_depth * 0.60 + lab_boost)


def score_core_domain(domain: str, smap: Dict, evidence: set, signals: Dict) -> int:
    core = DOMAIN_CORE.get(_norm(domain), [])
    if not core:
        return 0
    total = 0.0
    for want in core:
        hit = smap.get(want)
        if hit is None:
            # partial token match: "machine learning" vs "ml"
            for n in smap:
                if want in n or n in want:
                    hit = smap[n]
                    break
        total += _rated(hit, evidence) if hit else 0
    avg = total / len(core)
    mastery = signals.get("skillpath_mastery_avg", 0)   # 0-100 from progress_engine
    return _clamp(avg * 0.7 + mastery * 0.3) if mastery else _clamp(avg)


def score_projects(projects: List[Dict]) -> int:
    if not projects:
        return 0
    scored = []
    for p in projects:
        s = 0
        if _norm(p.get("title")):
            s += 15
        if len(_norm(p.get("description"))) >= 60:
            s += 20
        if len(p.get("tech") or []) >= 2:
            s += 15
        if p.get("github"):
            s += 15
        if p.get("deployed") and p.get("deployed_url"):
            s += 25
        elif p.get("deployed"):
            s += 12                       # claims deploy, no link -> half credit
        if _norm(p.get("metrics")):
            s += 10
        scored.append(min(100, s))
    scored.sort(reverse=True)
    top = scored[:3]
    avg = sum(top) / len(top)
    count_factor = min(1.0, 0.55 + 0.15 * len(scored))   # 1 proj=0.70, 3+=1.00
    return _clamp(avg * count_factor)


def score_deployment(projects: List[Dict], smap: Dict, evidence: set) -> int:
    deployed = sum(1 for p in (projects or []) if p.get("deployed"))
    live = sum(1 for p in (projects or []) if p.get("deployed") and p.get("deployed_url"))
    has_git = any(p.get("github") for p in (projects or []))
    tool = max((_rated(smap[n], evidence) for n in smap if n in DEPLOY_SKILLS), default=0)

    s = 0.0
    s += min(45, live * 25 + (deployed - live) * 10)
    s += 15 if has_git else 0
    s += tool * 0.40
    return _clamp(s)


def score_aptitude(profile: Dict, signals: Dict) -> int:
    platform = signals.get("aptitude_accuracy", 0)       # 0-100, real evidence
    if platform:
        return _clamp(platform)
    return min(UNEVIDENCED_CAP,
               LABEL_SCORE.get(_norm(profile.get("aptitude_self")), 40))


def score_communication(profile: Dict, signals: Dict) -> int:
    platform = signals.get("interview_avg_score", 0)     # 0-100 from Interview Studio
    sessions = signals.get("interview_sessions", 0)
    if platform and sessions:
        return _clamp(platform)
    return min(UNEVIDENCED_CAP,
               LABEL_SCORE.get(_norm(profile.get("communication_self")), 40))


def score_resume_ats(profile: Dict, signals: Dict) -> int:
    ats = signals.get("latest_ats_score", 0)             # 0-100 from Resume AI
    if ats:
        return _clamp(ats)
    text = _norm(profile.get("resume_text"))
    if not text:
        return 10
    s = 30
    if len(text) > 800:
        s += 10
    if profile.get("github_url"):
        s += 8
    if profile.get("linkedin_url"):
        s += 7
    return _clamp(s)


# ---------------------------------------------------------------- public API
DEFAULT_SIGNALS: Dict[str, int] = {
    "arena_solved": 0,
    "lab_completions": 0,
    "sql_lab_completions": 0,
    "skillpath_mastery_avg": 0,
    "aptitude_accuracy": 0,
    "interview_avg_score": 0,
    "interview_sessions": 0,
    "latest_ats_score": 0,
}

# How much each pillar counts toward the *overall* ATLAS Profile Score.
PROFILE_WEIGHTS: Dict[str, float] = {
    "programming": 0.15,
    "dsa": 0.20,
    "database_sql": 0.10,
    "core_domain": 0.20,
    "projects": 0.13,
    "deployment": 0.07,
    "aptitude": 0.05,
    "communication": 0.05,
    "resume_ats": 0.05,
}


def compute_pillars(profile: Dict[str, Any],
                    signals: Dict[str, int] | None = None) -> Dict[str, int]:
    """profile = plain dict of CareerProfileIn fields. Returns {pillar: 0-100}."""
    sig = {**DEFAULT_SIGNALS, **(signals or {})}
    skills = profile.get("skills") or []
    projects = profile.get("projects") or []
    internships = profile.get("internships") or []

    smap = _skill_map(skills)
    evidence = _evidence_terms(projects, internships, profile)

    return {
        "programming": score_programming(smap, evidence, sig),
        "dsa": score_dsa(
            int(profile.get("leetcode_easy") or 0),
            int(profile.get("leetcode_medium") or 0),
            int(profile.get("leetcode_hard") or 0),
            sig["arena_solved"],
        ),
        "database_sql": score_database_sql(profile, smap, evidence, sig),
        "core_domain": score_core_domain(profile.get("target_domain"), smap, evidence, sig),
        "projects": score_projects(projects),
        "deployment": score_deployment(projects, smap, evidence),
        "aptitude": score_aptitude(profile, sig),
        "communication": score_communication(profile, sig),
        "resume_ats": score_resume_ats(profile, sig),
    }


def compute_profile_score(pillars: Dict[str, int]) -> int:
    total = sum(PROFILE_WEIGHTS[p] * pillars.get(p, 0) for p in PILLARS)
    return _clamp(total)


def profile_grade(score: int) -> str:
    if score >= 80:
        return "Placement Ready"
    if score >= 65:
        return "Nearly There"
    if score >= 50:
        return "Building"
    if score >= 30:
        return "Early Stage"
    return "Just Started"


def fingerprint(profile: Dict[str, Any],
                target_slugs: List[str],
                pillars: Dict[str, int],
                bench_version: str = "v12.1") -> str:
    """
    Stable sha256 over everything that could change the analysis.
    Same inputs -> same fingerprint -> cached report -> ZERO AI calls.
    """
    payload = {
        "d": _norm(profile.get("target_domain")),
        "t": sorted(target_slugs),
        "p": {k: pillars.get(k, 0) for k in PILLARS},
        "lc": [profile.get("leetcode_easy") or 0,
               profile.get("leetcode_medium") or 0,
               profile.get("leetcode_hard") or 0],
        "sq": _norm(profile.get("sql_level")),
        "pr": len(profile.get("projects") or []),
        "dep": sum(1 for p in (profile.get("projects") or []) if p.get("deployed")),
        "sk": sorted(_norm(s.get("name")) + ":" + _norm(s.get("label"))
                     for s in (profile.get("skills") or [])),
        "v": bench_version,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()
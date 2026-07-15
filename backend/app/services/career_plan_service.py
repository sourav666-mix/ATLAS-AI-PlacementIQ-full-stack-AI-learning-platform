"""
ATLAS AI v12 — Career Plan service.

THE ONLY TYPE-B SURFACE IN THIS MODULE.
Exactly ONE bounded AI call, and only when `fingerprint` is not already cached.
Same profile -> same fingerprint -> DB read -> zero cost, forever.

CLOSED-LOOP GUARANTEE: the AI may only reference action_ids from ATLAS_ACTIONS.
Anything it invents (Coursera, Udemy, "watch a YouTube playlist") is DROPPED by
_sanitize_plan() before the response is built. The student can therefore only be
sent to routes that exist inside this platform.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career_target import CareerGapReport
from app.services.ai_provider_router import complete as ask_ai, parse_json
from app.services.gap_engine_service import critical_pillars, gap_summary_line
from app.services.profile_score_service import PILLAR_LABELS, profile_grade

# ---------------------------------------------------------------------------
# INTERNAL ACTION ALLOW-LIST — every path a student can be sent down.
# route values must match frontend/src/App.jsx routes.
# ---------------------------------------------------------------------------
ATLAS_ACTIONS: Dict[str, List[Dict[str, Any]]] = {
    "programming": [
        {"action_id": "skillpath_lang", "label": "SkillPath — language fundamentals track",
         "route": "/skillpath", "est_hours": 20},
        {"action_id": "livelab_python", "label": "Live Lab — write & run real code in-browser",
         "route": "/live-lab", "est_hours": 12},
    ],
    "dsa": [
        {"action_id": "arena_easy", "label": "Code Arena — Easy pattern drills",
         "route": "/code-arena?difficulty=Easy", "est_hours": 15},
        {"action_id": "arena_medium", "label": "Code Arena — Medium patterns (arrays, DP, graphs)",
         "route": "/code-arena?difficulty=Medium", "est_hours": 30},
        {"action_id": "arena_hard", "label": "Code Arena — Advanced set",
         "route": "/code-arena?difficulty=Advanced", "est_hours": 25},
    ],
    "database_sql": [
        {"action_id": "skillpath_sql", "label": "SkillPath — SQL topic (joins → window functions)",
         "route": "/skillpath?topic=sql", "est_hours": 14},
        {"action_id": "livelab_sql", "label": "Live Lab — SQL sandbox on real datasets",
         "route": "/live-lab?engine=sql", "est_hours": 10},
        {"action_id": "arena_sql", "label": "Code Arena — SQL query problems",
         "route": "/code-arena?category=sql", "est_hours": 8},
    ],
    "core_domain": [
        {"action_id": "skillpath_core", "label": "SkillPath — your domain roadmap, phase by phase",
         "route": "/skillpath", "est_hours": 40},
        {"action_id": "livelab_domain", "label": "Live Lab — graded domain labs",
         "route": "/live-lab", "est_hours": 20},
        {"action_id": "company_intel", "label": "Company Intel — what this company actually asks",
         "route": "/company-intel", "est_hours": 2},
    ],
    "projects": [
        {"action_id": "capstone", "label": "SkillPath Capstone — guided end-to-end project",
         "route": "/skillpath?phase=capstone", "est_hours": 35},
        {"action_id": "livelab_artifact", "label": "Live Lab — export a trained model / cleaned dataset",
         "route": "/live-lab", "est_hours": 10},
    ],
    "deployment": [
        {"action_id": "skillpath_deploy", "label": "SkillPath — Git & Deployment track",
         "route": "/skillpath?topic=deployment", "est_hours": 12},
        {"action_id": "lab_deploy_task", "label": "Live Lab — ship your project & add the live URL",
         "route": "/live-lab?task=deploy", "est_hours": 8},
    ],
    "aptitude": [
        {"action_id": "assessment_aptitude", "label": "Assessment Center — daily aptitude sets",
         "route": "/assessment?mode=aptitude", "est_hours": 15},
        {"action_id": "championship", "label": "Weekly Championship — timed, proctored practice",
         "route": "/championship", "est_hours": 4},
    ],
    "communication": [
        {"action_id": "interview_studio", "label": "AI Interview Studio — voice mock interviews",
         "route": "/interview-studio", "est_hours": 10},
        {"action_id": "interview_hr", "label": "Interview Studio — HR & behavioural round",
         "route": "/interview-studio?level=hr", "est_hours": 5},
    ],
    "resume_ats": [
        {"action_id": "resume_builder", "label": "Resume AI — build an ATS-safe resume",
         "route": "/resume?mode=build", "est_hours": 3},
        {"action_id": "resume_analyzer", "label": "Resume AI — analyse against the target JD",
         "route": "/resume?mode=analyze", "est_hours": 2},
        {"action_id": "jobs_board", "label": "Jobs Board — apply with your match score",
         "route": "/jobs", "est_hours": 2},
    ],
}

_ACTION_INDEX: Dict[str, Dict[str, Any]] = {
    a["action_id"]: {**a, "pillar": pillar}
    for pillar, acts in ATLAS_ACTIONS.items()
    for a in acts
}

PLAN_WEEKS = 12


# ---------------------------------------------------------------------------
# Deterministic fallback plan — used if the AI call fails. Still 100% usable.
# ---------------------------------------------------------------------------
def build_fallback_plan(pillars: Dict[str, int],
                        gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
    focus = critical_pillars(gaps, top_n=4) or ["core_domain", "dsa"]

    strengths = [f"{PILLAR_LABELS[p]} ({v}/100)"
                 for p, v in sorted(pillars.items(), key=lambda kv: kv[1], reverse=True)
                 if v >= 60][:3] or ["You have a clear target — that's the starting advantage."]

    critical = []
    for p in focus:
        critical.append(f"{PILLAR_LABELS[p]} — currently {pillars.get(p, 0)}/100 "
                        f"and it is the biggest single blocker for your targets.")

    weeks: List[Dict[str, Any]] = []
    rotation = [p for p in focus for _ in range(3)][:PLAN_WEEKS]
    while len(rotation) < PLAN_WEEKS:
        rotation.append(focus[len(rotation) % len(focus)])

    for i in range(PLAN_WEEKS):
        pillar = rotation[i]
        acts = ATLAS_ACTIONS.get(pillar, [])
        chosen = acts[i % len(acts)] if acts else None
        actions = []
        if chosen:
            actions.append({
                "action_id": chosen["action_id"],
                "label": chosen["label"],
                "route": chosen["route"],
                "pillar": pillar,
                "why": f"Closes your {PILLAR_LABELS[pillar]} gap "
                       f"({pillars.get(pillar, 0)}/100 today).",
                "est_hours": chosen["est_hours"],
            })
        weeks.append({
            "week": i + 1,
            "theme": PILLAR_LABELS.get(pillar, "Focus"),
            "actions": actions,
            "checkpoint": f"Re-run your gap analysis — {PILLAR_LABELS[pillar]} should move up.",
        })

    return {
        "headline": gap_summary_line(gaps),
        "strengths": strengths,
        "critical_gaps": critical,
        "company_notes": {
            g["company_slug"]:
                f"{g['gap_pct']}% to close. {g['verdict']}. "
                f"Biggest lever: {g['pillar_gaps'][0]['label']}."
            for g in gaps
        },
        "plan": weeks,
    }


# ---------------------------------------------------------------------------
# Sanitizer — this is what makes the closed loop STRUCTURAL, not a promise.
# ---------------------------------------------------------------------------
def _sanitize_plan(raw: Dict[str, Any], pillars: Dict[str, int],
                   gaps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None

    weeks_in = raw.get("plan") or []
    if not isinstance(weeks_in, list) or not weeks_in:
        return None

    valid_slugs = {g["company_slug"] for g in gaps}
    clean_weeks: List[Dict[str, Any]] = []

    for idx, w in enumerate(weeks_in[:PLAN_WEEKS]):
        if not isinstance(w, dict):
            continue
        actions_out = []
        for a in (w.get("actions") or [])[:3]:
            if not isinstance(a, dict):
                continue
            aid = str(a.get("action_id") or "").strip()
            known = _ACTION_INDEX.get(aid)
            if not known:
                continue                       # <-- external / invented action DROPPED
            actions_out.append({
                "action_id": aid,
                "label": known["label"],       # label/route come from OUR table, not the AI
                "route": known["route"],
                "pillar": known["pillar"],
                "why": str(a.get("why") or "")[:240]
                       or f"Closes your {PILLAR_LABELS[known['pillar']]} gap.",
                "est_hours": int(known["est_hours"]),
            })
        if not actions_out:
            continue
        clean_weeks.append({
            "week": int(w.get("week") or idx + 1),
            "theme": str(w.get("theme") or "Focus")[:80],
            "actions": actions_out,
            "checkpoint": str(w.get("checkpoint") or "Re-run gap analysis.")[:200],
        })

    if not clean_weeks:
        return None

    notes_in = raw.get("company_notes") or {}
    company_notes = {
        s: str(notes_in.get(s, ""))[:400]
        for s in valid_slugs
        if isinstance(notes_in, dict)
    }
    for g in gaps:   # guarantee every target has a note
        if not company_notes.get(g["company_slug"]):
            company_notes[g["company_slug"]] = (
                f"{g['gap_pct']}% to close. {g['verdict']}."
            )

    return {
        "headline": str(raw.get("headline") or gap_summary_line(gaps))[:300],
        "strengths": [str(s)[:200] for s in (raw.get("strengths") or [])][:5]
                     or ["Clear target chosen."],
        "critical_gaps": [str(s)[:250] for s in (raw.get("critical_gaps") or [])][:6]
                         or [f"{PILLAR_LABELS[p]} is your biggest blocker."
                             for p in critical_pillars(gaps, 3)],
        "company_notes": company_notes,
        "plan": clean_weeks,
    }


def _build_prompt(profile: Dict[str, Any], pillars: Dict[str, int],
                  gaps: List[Dict[str, Any]]) -> str:
    allowed = [
        {"action_id": a["action_id"], "pillar": p, "label": a["label"]}
        for p, acts in ATLAS_ACTIONS.items() for a in acts
    ]
    gap_view = [{
        "company": g["company_name"],
        "slug": g["company_slug"],
        "gap_pct": g["gap_pct"],
        "verdict": g["verdict"],
        "top_gaps": [
            {"pillar": b["pillar"], "have": b["have"], "need": b["need"]}
            for b in g["pillar_gaps"][:4] if b["gap"] > 0
        ],
    } for g in gaps]

    return f"""You are the ATLAS AI career coach for Indian B.Tech placement students.

STUDENT
name: {profile.get('full_name') or 'Student'}
branch/specialization: {profile.get('branch')} / {profile.get('specialization')}
target domain: {profile.get('target_domain')}
LeetCode: {profile.get('leetcode_easy',0)}E / {profile.get('leetcode_medium',0)}M / {profile.get('leetcode_hard',0)}H
SQL level: {profile.get('sql_level')}
projects: {len(profile.get('projects') or [])} ({sum(1 for p in (profile.get('projects') or []) if p.get('deployed'))} deployed)

PILLAR SCORES (0-100, already computed by us — do NOT recompute or contradict them)
{json.dumps(pillars, indent=1)}

COMPANY GAPS (already computed by us — quote these numbers exactly)
{json.dumps(gap_view, indent=1)}

ALLOWED ACTIONS — you may ONLY use these action_id values. Nothing else exists.
{json.dumps(allowed)}

TASK
Write a {PLAN_WEEKS}-week closing plan. Every week must contain 1-2 actions, each
referencing an action_id from the allowed list above. Attack the highest-gap pillars
first. Never mention any website, course, book, or platform outside ATLAS AI.

Respond with ONLY this JSON. No markdown, no preamble:
{{
 "headline": "one line naming each company and its gap %",
 "strengths": ["2-4 concrete strengths, quoting their real numbers"],
 "critical_gaps": ["3-5 blockers, each naming the pillar and the number"],
 "company_notes": {{"<slug>": "what THIS company specifically wants that they lack"}},
 "plan": [
   {{"week":1,"theme":"...","actions":[
      {{"action_id":"arena_easy","why":"one specific sentence"}}],
     "checkpoint":"how they know week 1 worked"}}
 ]
}}"""


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
async def get_or_create_report(db: AsyncSession, *, user_id: str, profile_id: str,
                               fingerprint: str, profile: Dict[str, Any],
                               pillars: Dict[str, int], gaps: List[Dict[str, Any]],
                               force: bool = False) -> Dict[str, Any]:
    """
    Returns the gap report. Makes AT MOST ONE AI call, and only on a cache miss.
    """
    if not force:
        res = await db.execute(
            select(CareerGapReport).where(
                CareerGapReport.user_id == user_id,
                CareerGapReport.fingerprint == fingerprint,
            )
        )
        cached: Optional[CareerGapReport] = res.scalar_one_or_none()
        if cached:
            body = dict(cached.report_json or {})
            body["fingerprint"] = fingerprint
            body["source"] = "cache"
            body["generated_at"] = cached.created_at.isoformat() if cached.created_at else None
            return body

    # ---- the single Type-B call -------------------------------------------
    source = "ai"
    model_used = ""
    plan: Optional[Dict[str, Any]] = None
    try:
        raw_text = await ask_ai(_build_prompt(profile, pillars, gaps))
        if isinstance(raw_text, dict):                # some routers return dicts
            model_used = str(raw_text.get("model", ""))
            raw_text = raw_text.get("text") or raw_text.get("content") or ""
        parsed = parse_json(raw_text)
        plan = _sanitize_plan(parsed, pillars, gaps)
    except Exception:
        plan = None

    if plan is None:
        plan = build_fallback_plan(pillars, gaps)
        source = "fallback"

    plan["profile_score"] = int(round(
        sum(pillars.values()) / max(1, len(pillars))
    )) if "profile_score" not in plan else plan["profile_score"]
    plan["grade"] = profile_grade(int(plan["profile_score"]))

    row = CareerGapReport(
        user_id=user_id,
        profile_id=profile_id,
        fingerprint=fingerprint,
        report_json=plan,
        source=source,
        model_used=model_used[:60],
    )
    db.add(row)
    await db.commit()

    out = dict(plan)
    out["fingerprint"] = fingerprint
    out["source"] = source
    out["generated_at"] = datetime.utcnow().isoformat()
    return out
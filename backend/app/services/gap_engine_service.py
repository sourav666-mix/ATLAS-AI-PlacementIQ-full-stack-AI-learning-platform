"""
ATLAS AI v12 — Gap Engine. PURE MATH, ZERO AI.

readiness = SUM( weight_p * min(1, have_p / need_p) )      -> 0..1
gap_pct   = 100 - round(readiness * 100)

Deterministic, explainable, and identical for two identical profiles.
This is what powers "Amazon: 60% to close, TCS: 35%, Deloitte: 45%".
"""
from __future__ import annotations

from typing import Any, Dict, List

from app.services.profile_score_service import PILLARS, PILLAR_LABELS


def _verdict(gap: int) -> str:
    if gap <= 15:
        return "Ready to apply"
    if gap <= 30:
        return "Close — polish and apply"
    if gap <= 50:
        return "Reachable — focused work needed"
    if gap <= 70:
        return "Stretch — significant gap"
    return "Long shot — build fundamentals first"


def compute_company_gap(pillars: Dict[str, int],
                        benchmark: Dict[str, Any]) -> Dict[str, Any]:
    """One company. Returns readiness, gap and a per-pillar breakdown."""
    reqs: Dict[str, int] = benchmark["requirements"]
    weights: Dict[str, float] = benchmark["weights"]

    readiness = 0.0
    breakdown: List[Dict[str, Any]] = []

    for p in PILLARS:
        have = int(pillars.get(p, 0))
        need = max(1, int(reqs.get(p, 60)))
        w = float(weights.get(p, 0.0))

        ratio = min(1.0, have / need)
        readiness += w * ratio

        gap_p = max(0, need - have)
        deficit = round(w * (1.0 - ratio) * 100, 2)   # weighted points lost

        breakdown.append({
            "pillar": p,
            "label": PILLAR_LABELS[p],
            "have": have,
            "need": need,
            "gap": gap_p,
            "weight": round(w, 4),
            "deficit_points": deficit,
        })

    readiness_pct = int(round(readiness * 100))
    readiness_pct = max(0, min(100, readiness_pct))
    gap_pct = 100 - readiness_pct

    # Biggest levers first — this ordering drives the learning plan.
    breakdown.sort(key=lambda b: b["deficit_points"], reverse=True)

    return {
        "company_slug": benchmark["company_slug"],
        "company_name": benchmark["company_name"],
        "hiring_bar": benchmark["hiring_bar"],
        "readiness_pct": readiness_pct,
        "gap_pct": gap_pct,
        "verdict": _verdict(gap_pct),
        "pillar_gaps": breakdown,
        "process": benchmark.get("process", []),
        "focus_notes": benchmark.get("focus_notes", ""),
    }


def compute_all_gaps(pillars: Dict[str, int],
                     benchmarks: List[Dict[str, Any]],
                     priorities: Dict[str, int] | None = None) -> List[Dict[str, Any]]:
    pr = priorities or {}
    out = []
    for b in benchmarks:
        g = compute_company_gap(pillars, b)
        g["priority"] = int(pr.get(b["company_slug"], 1))
        out.append(g)
    out.sort(key=lambda g: (g["priority"], g["gap_pct"]))
    return out


def critical_pillars(gaps: List[Dict[str, Any]], top_n: int = 4) -> List[str]:
    """
    Pillars that hurt the MOST across ALL chosen companies.
    Summing weighted deficits means one shared plan closes three gaps at once.
    """
    agg: Dict[str, float] = {p: 0.0 for p in PILLARS}
    for g in gaps:
        for b in g["pillar_gaps"]:
            if b["gap"] > 0:
                agg[b["pillar"]] += b["deficit_points"]
    ranked = sorted(agg.items(), key=lambda kv: kv[1], reverse=True)
    return [p for p, v in ranked if v > 0][:top_n]


def gap_summary_line(gaps: List[Dict[str, Any]]) -> str:
    """e.g. 'Amazon 60% to close · Deloitte 45% · TCS 35%'"""
    return " · ".join(f"{g['company_name']} {g['gap_pct']}% to close" for g in gaps)
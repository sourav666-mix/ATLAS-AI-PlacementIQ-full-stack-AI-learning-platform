"""
Double-check harness for the Career Target & Gap Engine.
NO DB, NO NETWORK, NO AI — every assertion is pure math.

    pytest backend/tests/test_career_target.py -v
"""
import pytest

from app.services import gap_engine_service as gapx
from app.services import profile_score_service as sc
from app.services.career_plan_service import (
    ATLAS_ACTIONS, _ACTION_INDEX, _sanitize_plan, build_fallback_plan,
)
from app.services.company_benchmark_service import (
    normalize_requirements, normalize_weights,
)
from app.scripts.seed_company_benchmarks import _build


# --------------------------------------------------------------- fixtures
def rahul():
    """The example student: B.Tech CSE, Data Science target."""
    return {
        "full_name": "Rahul",
        "branch": "CSE",
        "specialization": "Core CSE",
        "target_domain": "data_science",
        "leetcode_easy": 60, "leetcode_medium": 25, "leetcode_hard": 2,
        "sql_level": "basic",
        "sql_details": "select, where, group by, joins",
        "aptitude_self": "learning",
        "communication_self": "learning",
        "skills": [
            {"name": "python", "category": "language", "label": "strong",
             "details": "3 semesters", "evidence": "used in both projects"},
            {"name": "pandas", "category": "library", "label": "comfortable"},
            {"name": "numpy", "category": "library", "label": "comfortable"},
            {"name": "sql", "category": "database", "label": "learning"},
            {"name": "machine learning", "category": "core", "label": "learning"},
            {"name": "git", "category": "tool", "label": "comfortable"},
        ],
        "projects": [
            {"title": "Movie Recommender", "description": "Content-based recommender "
             "built on the MovieLens dataset with cosine similarity over TF-IDF vectors.",
             "tech": ["python", "pandas", "scikit-learn"], "github": "https://github.com/x/y",
             "deployed": False, "deployed_url": None, "metrics": None},
            {"title": "Sales Dashboard", "description": "Cleaned 40k rows of retail sales "
             "and produced monthly trend charts with matplotlib.",
             "tech": ["python", "pandas", "matplotlib"], "github": "https://github.com/x/z",
             "deployed": False, "deployed_url": None, "metrics": None},
        ],
        "internships": [],
        "certifications": [],
        "resume_text": None,
    }


def bench_for(slug):
    name = {"amazon": "Amazon", "tcs": "TCS", "deloitte": "Deloitte"}[slug]
    arch = {"amazon": "product_faang", "tcs": "service_mass",
            "deloitte": "consulting"}[slug]
    row = _build(slug, name, arch, "data_science")
    return {
        "company_slug": row.company_slug,
        "company_name": row.company_name,
        "hiring_bar": row.hiring_bar,
        "requirements": normalize_requirements(row.requirements_json),
        "weights": normalize_weights(row.weights_json),
        "process": row.process_json,
        "focus_notes": row.focus_notes,
    }


# --------------------------------------------------------------- pillars
def test_pillars_bounded_and_complete():
    p = sc.compute_pillars(rahul())
    assert set(p) == set(sc.PILLARS)
    assert all(0 <= v <= 100 for v in p.values())


def test_dsa_math_is_exact():
    # 60*1 + 25*2.5 + 2*5 = 132.5 ; /4.5 = 29.4 -> 29
    assert sc.score_dsa(60, 25, 2) == 29
    assert sc.score_dsa(0, 0, 0) == 0
    assert sc.score_dsa(500, 500, 500) == 100          # clamped


def test_unevidenced_claims_are_capped():
    """A student who ticks 'expert' with no project behind it cannot score 95."""
    inflated = rahul()
    inflated["skills"] = [{"name": "kubernetes", "category": "cloud", "label": "expert"}]
    inflated["projects"] = []
    p = sc.compute_pillars(inflated)
    assert p["deployment"] <= sc.UNEVIDENCED_CAP


def test_deploying_a_project_raises_deployment_score():
    before = sc.compute_pillars(rahul())["deployment"]
    after_profile = rahul()
    after_profile["projects"][0]["deployed"] = True
    after_profile["projects"][0]["deployed_url"] = "https://demo.example.com"
    after = sc.compute_pillars(after_profile)["deployment"]
    assert after > before, "Deploying a project must move the deployment pillar"


def test_profile_score_and_grade():
    p = sc.compute_pillars(rahul())
    s = sc.compute_profile_score(p)
    assert 0 <= s <= 100
    assert sc.profile_grade(s) in {
        "Just Started", "Early Stage", "Building", "Nearly There", "Placement Ready"}


# --------------------------------------------------------------- gaps
def test_rahul_gap_ordering_matches_reality():
    """
    Amazon (DSA-heavy, 92 bar) must be the hardest for Rahul.
    TCS (aptitude-led, 58 bar) must be the easiest. Deloitte in between.
    """
    pillars = sc.compute_pillars(rahul())
    gaps = {b["company_slug"]: gapx.compute_company_gap(pillars, b)
            for b in (bench_for("amazon"), bench_for("tcs"), bench_for("deloitte"))}

    a = gaps["amazon"]["gap_pct"]
    t = gaps["tcs"]["gap_pct"]
    d = gaps["deloitte"]["gap_pct"]

    assert a > d > t, f"expected amazon > deloitte > tcs, got {a}/{d}/{t}"
    assert all(0 <= v <= 100 for v in (a, t, d))
    assert gaps["amazon"]["readiness_pct"] + a == 100


def test_dsa_is_amazons_top_lever_for_rahul():
    pillars = sc.compute_pillars(rahul())
    g = gapx.compute_company_gap(pillars, bench_for("amazon"))
    assert g["pillar_gaps"][0]["pillar"] == "dsa"


def test_gaps_shrink_when_the_student_improves():
    pillars = sc.compute_pillars(rahul())
    before = gapx.compute_company_gap(pillars, bench_for("amazon"))["gap_pct"]

    grinder = rahul()
    grinder["leetcode_easy"] = 150
    grinder["leetcode_medium"] = 200
    grinder["leetcode_hard"] = 40
    after = gapx.compute_company_gap(
        sc.compute_pillars(grinder), bench_for("amazon"))["gap_pct"]

    assert after < before


def test_critical_pillars_are_shared_across_all_three_targets():
    pillars = sc.compute_pillars(rahul())
    gaps = gapx.compute_all_gaps(
        pillars,
        [bench_for("amazon"), bench_for("tcs"), bench_for("deloitte")],
        {"amazon": 1, "tcs": 2, "deloitte": 3},
    )
    crit = gapx.critical_pillars(gaps, top_n=4)
    assert 1 <= len(crit) <= 4
    assert all(c in sc.PILLARS for c in crit)


# --------------------------------------------------------------- fingerprint
def test_fingerprint_is_stable_and_change_sensitive():
    p = rahul()
    pil = sc.compute_pillars(p)
    f1 = sc.fingerprint(p, ["amazon", "tcs"], pil)
    f2 = sc.fingerprint(p, ["tcs", "amazon"], pil)   # order must not matter
    assert f1 == f2 and len(f1) == 64

    p2 = rahul()
    p2["leetcode_medium"] = 90
    f3 = sc.fingerprint(p2, ["amazon", "tcs"], sc.compute_pillars(p2))
    assert f3 != f1, "A real profile change must invalidate the cached report"


# --------------------------------------------------------------- closed loop
def test_ai_cannot_send_students_outside_atlas():
    pillars = sc.compute_pillars(rahul())
    gaps = gapx.compute_all_gaps(pillars, [bench_for("amazon")], {"amazon": 1})

    hostile = {
        "headline": "x",
        "strengths": ["y"],
        "critical_gaps": ["z"],
        "company_notes": {"amazon": "grind"},
        "plan": [{
            "week": 1, "theme": "DSA", "checkpoint": "ok",
            "actions": [
                {"action_id": "arena_medium", "why": "close the DSA gap"},
                {"action_id": "buy_udemy_course", "why": "external!"},
                {"action_id": "watch_youtube", "why": "external!"},
            ],
        }],
    }
    clean = _sanitize_plan(hostile, pillars, gaps)
    ids = [a["action_id"] for w in clean["plan"] for a in w["actions"]]
    assert ids == ["arena_medium"]
    assert all(i in _ACTION_INDEX for i in ids)


def test_every_action_has_a_real_route():
    for pillar, acts in ATLAS_ACTIONS.items():
        assert pillar in sc.PILLARS
        for a in acts:
            assert a["route"].startswith("/")
            assert a["est_hours"] > 0


def test_fallback_plan_is_a_full_12_week_plan():
    pillars = sc.compute_pillars(rahul())
    gaps = gapx.compute_all_gaps(
        pillars, [bench_for("amazon"), bench_for("tcs")], {"amazon": 1, "tcs": 2})
    plan = build_fallback_plan(pillars, gaps)
    assert len(plan["plan"]) == 12
    assert all(w["actions"] for w in plan["plan"])
    assert set(plan["company_notes"]) == {"amazon", "tcs"}


# --------------------------------------------------------------- benchmarks
def test_all_seeded_weights_normalize_to_one():
    from app.scripts.seed_company_benchmarks import COMPANIES, DOMAINS
    for slug, name, arch in COMPANIES:
        for dom in DOMAINS:
            row = _build(slug, name, arch, dom)
            w = normalize_weights(row.weights_json)
            assert abs(sum(w.values()) - 1.0) < 0.001
            r = normalize_requirements(row.requirements_json)
            assert all(1 <= v <= 100 for v in r.values())
"""
OFFLINE SEEDER — TYPE A. Run once (and after any benchmark edit):

    python -m app.scripts.seed_company_benchmarks

Generates 12 companies x 9 domains = 108 benchmark rows from an
archetype base + a per-domain emphasis overlay. Deterministic, idempotent,
ZERO AI calls.
"""
import asyncio
from typing import Dict

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.models.career_target import CompanyBenchmark
from app.services.company_benchmark_service import (
    BENCHMARK_VERSION, normalize_requirements, normalize_weights,
)

# ---------------------------------------------------------------- archetypes
ARCHETYPES: Dict[str, Dict] = {
    "product_faang": {
        "hiring_bar": 92,
        "req": {"programming": 85, "dsa": 92, "database_sql": 70, "core_domain": 85,
                "projects": 80, "deployment": 70, "aptitude": 55, "communication": 72,
                "resume_ats": 70},
        "w": {"programming": 0.15, "dsa": 0.30, "database_sql": 0.06, "core_domain": 0.20,
              "projects": 0.12, "deployment": 0.06, "aptitude": 0.03, "communication": 0.05,
              "resume_ats": 0.03},
        "process": ["Online Assessment (2 DSA)", "1-2 DSA rounds", "Domain/System round",
                    "Bar-raiser / Leadership Principles"],
        "notes": "DSA is the gate. Nothing else compensates for it. Two solid Medium "
                 "problems in 90 minutes is the real bar.",
    },
    "product_mid": {
        "hiring_bar": 80,
        "req": {"programming": 78, "dsa": 78, "database_sql": 70, "core_domain": 78,
                "projects": 78, "deployment": 68, "aptitude": 55, "communication": 68,
                "resume_ats": 68},
        "w": {"programming": 0.16, "dsa": 0.24, "database_sql": 0.08, "core_domain": 0.20,
              "projects": 0.14, "deployment": 0.08, "aptitude": 0.03, "communication": 0.04,
              "resume_ats": 0.03},
        "process": ["Online Assessment", "DSA round", "Project deep-dive", "HR"],
        "notes": "Projects are interrogated hard. A deployed project with real numbers "
                 "beats a third clone project.",
    },
    "service_mass": {
        "hiring_bar": 58,
        "req": {"programming": 62, "dsa": 50, "database_sql": 62, "core_domain": 55,
                "projects": 55, "deployment": 40, "aptitude": 78, "communication": 72,
                "resume_ats": 65},
        "w": {"programming": 0.14, "dsa": 0.12, "database_sql": 0.12, "core_domain": 0.14,
              "projects": 0.10, "deployment": 0.04, "aptitude": 0.20, "communication": 0.10,
              "resume_ats": 0.04},
        "process": ["Aptitude + Verbal (NQT style)", "Coding (1-2 easy)",
                    "Technical Interview", "HR"],
        "notes": "Aptitude and communication carry the most weight. Clearing the cutoff "
                 "test matters more than DSA depth.",
    },
    "consulting": {
        "hiring_bar": 74,
        "req": {"programming": 68, "dsa": 60, "database_sql": 78, "core_domain": 76,
                "projects": 74, "deployment": 55, "aptitude": 70, "communication": 82,
                "resume_ats": 75},
        "w": {"programming": 0.11, "dsa": 0.12, "database_sql": 0.15, "core_domain": 0.19,
              "projects": 0.14, "deployment": 0.05, "aptitude": 0.09, "communication": 0.11,
              "resume_ats": 0.04},
        "process": ["Aptitude/Case screen", "SQL + domain technical",
                    "Case / business-problem round", "Partner HR"],
        "notes": "Business framing + SQL + a project you can explain to a non-engineer. "
                 "Communication is scored, not assumed.",
    },
}

COMPANIES = [
    ("amazon", "Amazon", "product_faang"),
    ("google", "Google", "product_faang"),
    ("microsoft", "Microsoft", "product_faang"),
    ("adobe", "Adobe", "product_mid"),
    ("flipkart", "Flipkart", "product_mid"),
    ("zoho", "Zoho", "product_mid"),
    ("tcs", "TCS", "service_mass"),
    ("infosys", "Infosys", "service_mass"),
    ("wipro", "Wipro", "service_mass"),
    ("cognizant", "Cognizant", "service_mass"),
    ("deloitte", "Deloitte", "consulting"),
    ("accenture", "Accenture", "consulting"),
]

DOMAINS = ["data_science", "data_analysis", "artificial_intelligence", "generative_ai",
           "frontend", "backend", "cloud", "mlops", "cybersecurity"]

# Per-domain requirement nudges (added to the archetype base, then clamped 1-100).
DOMAIN_OVERLAY: Dict[str, Dict[str, int]] = {
    "data_science":            {"database_sql": +10, "core_domain": +5, "dsa": -5, "deployment": -5},
    "data_analysis":           {"database_sql": +15, "dsa": -18, "core_domain": +5,
                                "communication": +8, "deployment": -12},
    "artificial_intelligence": {"core_domain": +10, "projects": +5, "database_sql": -5},
    "generative_ai":           {"core_domain": +8, "projects": +10, "dsa": -8, "deployment": +5},
    "frontend":                {"programming": +5, "projects": +10, "dsa": -10,
                                "deployment": +8, "database_sql": -12},
    "backend":                 {"database_sql": +10, "deployment": +8, "dsa": +3},
    "cloud":                   {"deployment": +20, "dsa": -12, "core_domain": +5,
                                "database_sql": -5},
    "mlops":                   {"deployment": +18, "core_domain": +5, "dsa": -8},
    "cybersecurity":           {"core_domain": +12, "deployment": +8, "dsa": -8,
                                "database_sql": -3},
}

# Weight nudges, renormalized afterwards.
DOMAIN_WEIGHT_OVERLAY: Dict[str, Dict[str, float]] = {
    "data_analysis": {"dsa": -0.08, "database_sql": +0.08, "communication": +0.02},
    "frontend":      {"dsa": -0.06, "projects": +0.06, "database_sql": -0.02},
    "cloud":         {"dsa": -0.06, "deployment": +0.08},
    "mlops":         {"dsa": -0.05, "deployment": +0.07},
    "backend":       {"database_sql": +0.04},
}


def _build(company_slug, company_name, archetype, domain):
    base = ARCHETYPES[archetype]
    req = dict(base["req"])
    for k, delta in DOMAIN_OVERLAY.get(domain, {}).items():
        req[k] = max(20, min(98, req[k] + delta))

    w = dict(base["w"])
    for k, delta in DOMAIN_WEIGHT_OVERLAY.get(domain, {}).items():
        w[k] = max(0.01, w[k] + delta)

    return CompanyBenchmark(
        company_slug=company_slug,
        company_name=company_name,
        archetype=archetype,
        domain_slug=domain,
        hiring_bar=base["hiring_bar"],
        requirements_json=normalize_requirements(req),
        weights_json=normalize_weights(w),
        process_json=base["process"],
        focus_notes=base["notes"],
        benchmark_version=BENCHMARK_VERSION,
    )


async def seed():
    created = updated = 0
    async with AsyncSessionLocal() as db:
        for slug, name, arch in COMPANIES:
            for domain in DOMAINS:
                row = _build(slug, name, arch, domain)
                existing = await db.execute(
                    select(CompanyBenchmark).where(
                        CompanyBenchmark.company_slug == slug,
                        CompanyBenchmark.domain_slug == domain,
                    )
                )
                found = existing.scalar_one_or_none()
                if found:
                    found.company_name = row.company_name
                    found.archetype = row.archetype
                    found.hiring_bar = row.hiring_bar
                    found.requirements_json = row.requirements_json
                    found.weights_json = row.weights_json
                    found.process_json = row.process_json
                    found.focus_notes = row.focus_notes
                    found.benchmark_version = row.benchmark_version
                    updated += 1
                else:
                    db.add(row)
                    created += 1
        await db.commit()

    print(f"[seed_company_benchmarks] created={created} updated={updated} "
          f"total={len(COMPANIES) * len(DOMAINS)} version={BENCHMARK_VERSION}")


if __name__ == "__main__":
    asyncio.run(seed())
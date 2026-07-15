"""
ATLAS AI v12 — Company Benchmark service. TYPE A ONLY.
Reads pre-seeded rows from company_benchmarks. Never calls AI.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.career_target import CompanyBenchmark
from app.services.profile_score_service import PILLARS

BENCHMARK_VERSION = "v12.1"

# Safety net: if a company/domain row is missing from the DB, we still return a
# sane, deterministic benchmark instead of 500-ing.
GENERIC_REQUIREMENTS: Dict[str, int] = {
    "programming": 70, "dsa": 65, "database_sql": 60, "core_domain": 70,
    "projects": 65, "deployment": 50, "aptitude": 55, "communication": 60,
    "resume_ats": 60,
}
GENERIC_WEIGHTS: Dict[str, float] = {
    "programming": 0.15, "dsa": 0.20, "database_sql": 0.10, "core_domain": 0.20,
    "projects": 0.13, "deployment": 0.07, "aptitude": 0.05, "communication": 0.05,
    "resume_ats": 0.05,
}


def normalize_weights(weights: Dict[str, Any]) -> Dict[str, float]:
    """Force weights onto the 9 pillars and renormalize to exactly 1.0."""
    clean = {p: float(weights.get(p, 0) or 0) for p in PILLARS}
    total = sum(clean.values())
    if total <= 0:
        return dict(GENERIC_WEIGHTS)
    return {p: round(v / total, 6) for p, v in clean.items()}


def normalize_requirements(reqs: Dict[str, Any]) -> Dict[str, int]:
    out = {}
    for p in PILLARS:
        try:
            v = int(reqs.get(p, GENERIC_REQUIREMENTS[p]))
        except (TypeError, ValueError):
            v = GENERIC_REQUIREMENTS[p]
        out[p] = max(1, min(100, v))     # never 0 -> avoids divide-by-zero
    return out


def _as_dict(row: CompanyBenchmark) -> Dict[str, Any]:
    return {
        "company_slug": row.company_slug,
        "company_name": row.company_name,
        "archetype": row.archetype or "product",
        "domain_slug": row.domain_slug,
        "hiring_bar": int(row.hiring_bar or 70),
        "requirements": normalize_requirements(row.requirements_json or {}),
        "weights": normalize_weights(row.weights_json or {}),
        "process": list(row.process_json or []),
        "focus_notes": row.focus_notes or "",
        "benchmark_version": row.benchmark_version or BENCHMARK_VERSION,
    }


def _synthetic(company_slug: str, domain_slug: str) -> Dict[str, Any]:
    name = company_slug.replace("-", " ").replace("_", " ").title()
    return {
        "company_slug": company_slug,
        "company_name": name,
        "archetype": "product",
        "domain_slug": domain_slug,
        "hiring_bar": 70,
        "requirements": dict(GENERIC_REQUIREMENTS),
        "weights": dict(GENERIC_WEIGHTS),
        "process": ["Online Assessment", "Technical Round", "HR Round"],
        "focus_notes": "Generic benchmark (company not seeded yet).",
        "benchmark_version": BENCHMARK_VERSION,
    }


async def list_companies(db: AsyncSession, domain_slug: str) -> List[Dict[str, Any]]:
    """Companies a student can pick as a target for this domain. Type A."""
    res = await db.execute(
        select(CompanyBenchmark)
        .where(CompanyBenchmark.domain_slug == domain_slug)
        .order_by(CompanyBenchmark.hiring_bar.desc(), CompanyBenchmark.company_name)
    )
    rows = res.scalars().all()
    return [
        {
            "company_slug": r.company_slug,
            "company_name": r.company_name,
            "archetype": r.archetype or "product",
            "hiring_bar": int(r.hiring_bar or 70),
            "focus_notes": r.focus_notes or "",
        }
        for r in rows
    ]


async def get_benchmark(db: AsyncSession, company_slug: str,
                        domain_slug: str) -> Dict[str, Any]:
    res = await db.execute(
        select(CompanyBenchmark).where(
            CompanyBenchmark.company_slug == company_slug,
            CompanyBenchmark.domain_slug == domain_slug,
        )
    )
    row: Optional[CompanyBenchmark] = res.scalar_one_or_none()
    if row is None:
        # try any-domain row for that company before giving up
        res2 = await db.execute(
            select(CompanyBenchmark)
            .where(CompanyBenchmark.company_slug == company_slug)
            .limit(1)
        )
        row = res2.scalar_one_or_none()
    return _as_dict(row) if row else _synthetic(company_slug, domain_slug)


async def get_benchmarks(db: AsyncSession, company_slugs: List[str],
                         domain_slug: str) -> List[Dict[str, Any]]:
    return [await get_benchmark(db, slug, domain_slug) for slug in company_slugs]
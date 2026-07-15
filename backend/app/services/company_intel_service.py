# company_intel_service.py - [NEW] cache-first report generation + 30-day expiry
# backend/app/services/company_intel_service.py
"""Company Intel Pro — cache-first report engine.

Rule (v10, Phase 7): get_report(slug) returns the MySQL cache if it is fresh
(< 30 days), otherwise generates ONCE with the AI, stores it, and serves it.
There is NO per-student generation — every student reads the same cached report.
Refresh is age-triggered here (expiry) or admin-triggered later (admin panel).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.company import (
    CompanyListItem,
    CompanyReport,
    CompanyReportResponse,
)
from app.services import company_registry, prompts
from app.services.ai_provider_router import complete as ask_ai, parse_json

# --- INTEGRATION POINT ------------------------------------------------------
# The company_intel_cache model (created in Batch 3).
# Expected columns: id, company_slug, report_json (JSON), generated_at, expires_at
from app.models.company_intel import CompanyIntelCache  # noqa: E402
# ---------------------------------------------------------------------------

CACHE_DAYS = 30


def _now() -> datetime:
    # naive UTC — matches MySQL TIMESTAMP / SQLite defaults, avoids tz-compare bugs
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _get_row(db: AsyncSession, slug: str) -> CompanyIntelCache | None:
    res = await db.execute(
        select(CompanyIntelCache).where(CompanyIntelCache.company_slug == slug)
    )
    return res.scalar_one_or_none()


def _is_fresh(row: CompanyIntelCache | None) -> bool:
    return bool(row and row.expires_at and row.expires_at > _now())


async def _generate(company: dict) -> dict:
    """One live AI call → normalized report dict. Only place AI is used here."""
    system, message = prompts.build_company_intel_prompt(
        company["name"], company["sector"]
    )
    raw = await ask_ai(system, message)
    data = raw if isinstance(raw, dict) else parse_json(raw)
    if not isinstance(data, dict):
        raise HTTPException(status_code=502, detail="AI returned an unusable report")

    report = CompanyReport(**data)
    # stamp identity + guarantee the load-bearing field for the gap map
    report.slug = company["slug"]
    report.name = report.name or company["name"]
    report.sector = report.sector or company["sector"]
    if not report.required_skills:
        report.required_skills = list(report.tech_stack)
    return report.model_dump()


async def _store(db: AsyncSession, slug: str, report: dict) -> CompanyIntelCache:
    now = _now()
    expires = now + timedelta(days=CACHE_DAYS)
    row = await _get_row(db, slug)
    if row:
        row.report_json = report
        row.generated_at = now
        row.expires_at = expires
    else:
        row = CompanyIntelCache(
            id=str(uuid.uuid4()),
            company_slug=slug,
            report_json=report,
            generated_at=now,
            expires_at=expires,
        )
        db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


def _to_response(company: dict, row: CompanyIntelCache, *, cached: bool) -> CompanyReportResponse:
    return CompanyReportResponse(
        slug=company["slug"],
        name=company["name"],
        sector=company["sector"],
        cached=cached,
        generated_at=row.generated_at,
        expires_at=row.expires_at,
        report=CompanyReport(**(row.report_json or {})),
    )


async def get_report(db: AsyncSession, raw_slug: str, *, force: bool = False) -> CompanyReportResponse:
    slug = company_registry.resolve_slug(raw_slug)
    company = company_registry.get_company(slug) if slug else None
    if not company:
        raise HTTPException(status_code=404, detail=f"Unknown company '{raw_slug}'")

    row = await _get_row(db, slug)
    if _is_fresh(row) and not force:
        return _to_response(company, row, cached=True)

    report = await _generate(company)
    row = await _store(db, slug, report)
    return _to_response(company, row, cached=False)


async def get_report_dict(db: AsyncSession, raw_slug: str) -> tuple[dict, dict]:
    """Helper for gap map / compare: returns (company_meta, report_dict)."""
    resp = await get_report(db, raw_slug)
    return {"slug": resp.slug, "name": resp.name, "sector": resp.sector}, resp.report.model_dump()


async def list_available(db: AsyncSession) -> list[CompanyListItem]:
    rows = (await db.execute(select(CompanyIntelCache))).scalars().all()
    by_slug = {r.company_slug: r for r in rows}
    now = _now()
    items: list[CompanyListItem] = []
    for c in company_registry.list_companies():
        row = by_slug.get(c["slug"])
        cached = bool(row and row.expires_at and row.expires_at > now)
        age = None
        if row and row.generated_at:
            age = max((now - row.generated_at).days, 0)
        items.append(CompanyListItem(
            slug=c["slug"], name=c["name"], sector=c["sector"],
            cached=cached, report_age_days=age,
        ))
    return items
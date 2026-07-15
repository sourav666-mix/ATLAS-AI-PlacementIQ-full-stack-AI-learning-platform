# company.py - [MOD] Company Intel Pro; cache-first report + gap map
# backend/app/routers/company.py
"""Company Intel Pro — student endpoints.

  GET /company                     -> browsable list (+ which are cached)
  GET /company/compare?a=&b=       -> side-by-side of two companies
  GET /company/{slug}              -> full report (cache-first; first viewer warms it)
  GET /company/{slug}/gap-map      -> personal green/amber/red vs the caller's radar

Cache-first means a student view may trigger a one-time generation, but never a
per-student one — the result is cached for everyone for 30 days.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.company import (
    CompanyListResponse,
    CompanyReportResponse,
    CompareResponse,
    GapMapResponse,
)
from app.services import company_intel_service, company_registry, gap_map_service

router = APIRouter(prefix="/company", tags=["Company Intel Pro"])


@router.get("", response_model=CompanyListResponse)
@router.get("/", response_model=CompanyListResponse, include_in_schema=False)
@router.get("/list", response_model=CompanyListResponse, include_in_schema=False)
async def list_companies(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return CompanyListResponse(companies=await company_intel_service.list_available(db))


# NOTE: declared before "/{slug}" so "compare" isn't captured as a slug.
@router.get("/compare", response_model=CompareResponse)
async def compare_companies(
    a: str,
    b: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if company_registry.resolve_slug(a) == company_registry.resolve_slug(b):
        raise HTTPException(status_code=400, detail="Pick two different companies")
    company_a, report_a = await company_intel_service.get_report_dict(db, a)
    company_b, report_b = await company_intel_service.get_report_dict(db, b)
    return gap_map_service.compare(company_a, report_a, company_b, report_b)


@router.get("/{slug}", response_model=CompanyReportResponse)
@router.get("/report/{slug}", response_model=CompanyReportResponse, include_in_schema=False)
async def company_report(
    slug: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return await company_intel_service.get_report(db, slug)


@router.get("/{slug}/gap-map", response_model=GapMapResponse)
@router.get("/{slug}/gap", response_model=GapMapResponse, include_in_schema=False)
async def company_gap_map(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    company, report = await company_intel_service.get_report_dict(db, slug)
    radar = await gap_map_service.get_radar(db, current_user.id)
    return gap_map_service.build_gap_map(company, report, radar)
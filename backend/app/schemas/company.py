# backend/app/schemas/company.py
"""Company Intel Pro — request/response schemas (Pydantic v2).

The AI-generated report is stored as JSON, so `CompanyReport` is intentionally
permissive (extra="allow", most fields optional) — a partial LLM payload should
never 500 the endpoint. Only `required_skills` is load-bearing: the gap map
reads it, so the service guarantees it is always a list.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------- report sub-structures ----------
class InterviewRound(BaseModel):
    model_config = ConfigDict(extra="allow")
    name: str = ""
    focus: str = ""
    sample_questions: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)


class HiringPattern(BaseModel):
    model_config = ConfigDict(extra="allow")
    cgpa_cutoff: str = ""
    aptitude_style: str = ""
    coding_platform: str = ""
    hr_themes: list[str] = Field(default_factory=list)


class Packages(BaseModel):
    model_config = ConfigDict(extra="allow")
    average: str = ""
    highest: str = ""
    median: str = ""


class CompanyReport(BaseModel):
    """Shape the prompt targets and the service normalizes to."""
    model_config = ConfigDict(extra="allow")

    slug: str = ""
    name: str = ""
    sector: str = ""
    summary: str = ""

    business_lines: list[str] = Field(default_factory=list)
    india_offices: list[str] = Field(default_factory=list)
    headcount: str = ""
    tech_stack: list[str] = Field(default_factory=list)
    hiring_seasons: list[str] = Field(default_factory=list)

    packages: Packages = Field(default_factory=Packages)
    salary_bands: list[dict] = Field(default_factory=list)
    culture_signals: list[str] = Field(default_factory=list)
    negotiation_tips: list[str] = Field(default_factory=list)  # ex-"Salary Negotiate" value

    interview_process: list[InterviewRound] = Field(default_factory=list)
    hiring_pattern: HiringPattern = Field(default_factory=HiringPattern)
    prep_strategy: list[dict] = Field(default_factory=list)

    # load-bearing: gap map consumes this
    required_skills: list[str] = Field(default_factory=list)


# ---------- list / report responses ----------
class CompanyListItem(BaseModel):
    slug: str
    name: str
    sector: str = ""
    cached: bool = False
    report_age_days: Optional[int] = None


class CompanyListResponse(BaseModel):
    companies: list[CompanyListItem]


class CompanyReportResponse(BaseModel):
    slug: str
    name: str
    sector: str = ""
    cached: bool
    generated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    report: CompanyReport


# ---------- gap map ----------
class GapItem(BaseModel):
    skill: str
    status: str            # "ready" | "practice" | "missing"
    radar_score: Optional[int] = None
    fix_topic: Optional[str] = None
    fix_link: Optional[str] = None


class GapMapResponse(BaseModel):
    company_slug: str
    company_name: str
    readiness_pct: int
    counts: dict           # {"ready": int, "practice": int, "missing": int}
    items: list[GapItem]


# ---------- compare ----------
class CompareRow(BaseModel):
    metric: str
    a: str = ""
    b: str = ""


class CompareResponse(BaseModel):
    a_slug: str
    b_slug: str
    a_name: str
    b_name: str
    rows: list[CompareRow]
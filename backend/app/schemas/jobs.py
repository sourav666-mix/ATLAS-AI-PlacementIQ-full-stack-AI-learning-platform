# jobs.py - [NEW] JobCard, JobPostCreate, TrackingUpdate
# backend/app/schemas/jobs.py
"""Jobs & Internships Board — schemas (Pydantic v2).

Covers the student board (cards + detail + tracker), the tracking pipeline, and
the admin posting/analytics payloads. The match score is computed server-side
(no LLM); clients never send it.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

# allowed application stages (mirror job_tracking.stage)
STAGES = ["saved", "applied", "test", "interview", "offer", "rejected"]


# ---------- shared ----------
class Eligibility(BaseModel):
    model_config = ConfigDict(extra="allow")
    batches: list[str] = Field(default_factory=list)      # e.g. ["2025", "2026"]
    min_cgpa: Optional[str] = None                         # kept as string ("6.5+")
    branches: list[str] = Field(default_factory=list)      # e.g. ["CSE", "IT"]


class GapSkill(BaseModel):
    skill: str
    radar_score: Optional[int] = None
    fix_topic: Optional[str] = None
    fix_link: Optional[str] = None


# ---------- student board ----------
class JobCard(BaseModel):
    id: str
    kind: str                      # job | internship
    title: str
    company: str
    location: str = ""
    work_mode: str = ""            # onsite | remote | hybrid
    ctc_band: str = ""
    stipend: str = ""
    deadline: Optional[date] = None
    posted_at: Optional[datetime] = None

    skills: list[str] = Field(default_factory=list)
    match_score: int = 0
    match_band: str = "stretch"    # great | good | stretch
    tracked_stage: Optional[str] = None   # set if the student has saved/applied

    verified: bool = True          # platform post -> "Verified by ATLAS AI"
    badge: str = "Verified by ATLAS AI"
    prep_link: Optional[str] = None       # -> Company Intel Pro
    tailor_resume_link: Optional[str] = None  # -> Resume Analyzer with JD prefilled


class JobDetail(JobCard):
    description: str = ""
    apply_url: str = ""
    eligibility: Eligibility = Field(default_factory=Eligibility)
    gap: list[GapSkill] = Field(default_factory=list)  # populated when match < 60


class JobListResponse(BaseModel):
    count: int
    jobs: list[JobCard]


# ---------- tracking pipeline ----------
class TrackingUpdate(BaseModel):
    stage: str


class TrackerItem(BaseModel):
    job_id: str
    title: str
    company: str
    stage: str
    match_score: Optional[int] = None
    deadline: Optional[date] = None
    updated_at: Optional[datetime] = None


class TrackerBoard(BaseModel):
    # kanban columns keyed by stage
    columns: dict[str, list[TrackerItem]]


# ---------- admin posting ----------
class JobPostCreate(BaseModel):
    kind: str = "job"                       # job | internship
    title: str
    company: str
    location: str = ""
    work_mode: str = "onsite"
    ctc_band: str = ""
    stipend: str = ""
    required_skills: list[str] = Field(default_factory=list)
    eligibility: Eligibility = Field(default_factory=Eligibility)
    description: str = ""
    apply_url: str = ""
    deadline: Optional[date] = None
    visibility: str = "all"                 # all | college_only
    college_id: Optional[str] = None        # super admin only; ignored for college admin


class JobPostUpdate(BaseModel):
    kind: Optional[str] = None
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    work_mode: Optional[str] = None
    ctc_band: Optional[str] = None
    stipend: Optional[str] = None
    required_skills: Optional[list[str]] = None
    eligibility: Optional[Eligibility] = None
    description: Optional[str] = None
    apply_url: Optional[str] = None
    deadline: Optional[date] = None
    visibility: Optional[str] = None
    status: Optional[str] = None            # active | archived


class AdminJobRow(BaseModel):
    id: str
    kind: str
    title: str
    company: str
    visibility: str
    college_id: Optional[str] = None
    status: str
    deadline: Optional[date] = None
    saves: int = 0
    applies: int = 0
    created_at: Optional[datetime] = None


class PostingAnalytics(BaseModel):
    job_id: str
    title: str
    saves: int
    applies: int
    by_stage: dict[str, int]
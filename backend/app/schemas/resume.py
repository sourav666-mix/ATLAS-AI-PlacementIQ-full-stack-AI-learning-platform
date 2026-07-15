# backend/app/schemas/resume.py
"""Request/response models for Resume AI 2.0."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# --- analyze ----------------------------------------------------------------
class AnalyzeResult(BaseModel):
    document_id: str
    analysis_id: Optional[str] = None       # what the SPA passes to /rebuild
    ats_score: int
    jd_match_score: int
    match_score: Optional[int] = None       # SPA alias for jd_match_score
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    star_feedback: str
    top_questions: List[str] = []
    strengths: List[str] = []
    improvements: List[str] = []


# --- rebuild ------------------------------------------------------------------
class RebuildIn(BaseModel):
    analysis_id: str
    template: str = "classic"


# --- builder (Mode B) ---------------------------------------------------------
class BuilderExportIn(BaseModel):
    resume: dict
    template: str = "classic"
    pages: int = 1


class BuiltPdfOut(BaseModel):
    document_id: str
    template: Optional[str] = None
    pages: int = 1
    pdf_base64: Optional[str] = None


# --- build ------------------------------------------------------------------
class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    dates: Optional[str] = None
    bullets: List[str] = []


class EducationItem(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None


class ProjectItem(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class BuildIn(BaseModel):
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    experience: List[ExperienceItem] = []
    education: List[EducationItem] = []
    projects: List[ProjectItem] = []
    template: str = "classic_ats"  # classic_ats | modern_minimal | technical_compact


class BuildResult(BaseModel):
    document_id: str
    template: str
    pdf_url: str
    pages: int


# --- history ----------------------------------------------------------------
class ResumeDocOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    mode: str
    template: Optional[str] = None
    pdf_url: Optional[str] = None
    created_at: datetime


__all__ = [
    "AnalyzeResult", "RebuildIn", "BuilderExportIn", "BuiltPdfOut",
    "ExperienceItem", "EducationItem", "ProjectItem",
    "BuildIn", "BuildResult", "ResumeDocOut",
]
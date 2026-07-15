"""Pydantic v2 schemas for the Career Target & Gap Engine."""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_validator

SKILL_LABELS = ["beginner", "learning", "comfortable", "strong", "expert"]
SQL_LEVELS = ["none", "basic", "intermediate", "advanced"]


class SkillIn(BaseModel):
    name: str = Field(..., max_length=80)
    category: str = Field("other", max_length=40)   # language|library|database|cloud|tool|core|soft
    label: str = Field("learning")                  # SKILL_LABELS
    details: Optional[str] = Field(None, max_length=500)
    evidence: Optional[str] = Field(None, max_length=300)  # where they used it

    @field_validator("label")
    @classmethod
    def _label_ok(cls, v: str) -> str:
        v = (v or "").strip().lower()
        return v if v in SKILL_LABELS else "learning"


class ProjectIn(BaseModel):
    title: str = Field(..., max_length=150)
    description: Optional[str] = Field(None, max_length=1200)
    tech: List[str] = Field(default_factory=list)
    github: Optional[str] = None
    deployed: bool = False
    deployed_url: Optional[str] = None
    metrics: Optional[str] = Field(None, max_length=300)  # "94% accuracy on 10k rows"


class InternshipIn(BaseModel):
    company: str = Field(..., max_length=150)
    role: Optional[str] = Field(None, max_length=120)
    months: int = 0
    work: Optional[str] = Field(None, max_length=600)


class CertificationIn(BaseModel):
    name: str = Field(..., max_length=150)
    issuer: Optional[str] = Field(None, max_length=120)
    year: Optional[int] = None


class TargetCompanyIn(BaseModel):
    company_slug: str
    priority: int = Field(1, ge=1, le=3)


class CareerProfileIn(BaseModel):
    full_name: Optional[str] = None
    degree: str = "B.Tech"
    branch: Optional[str] = None
    specialization: Optional[str] = None
    college: Optional[str] = None
    graduation_year: Optional[int] = None
    cgpa: Optional[float] = Field(None, ge=0, le=10)

    target_domain: str

    leetcode_username: Optional[str] = None
    leetcode_easy: int = Field(0, ge=0, le=3000)
    leetcode_medium: int = Field(0, ge=0, le=3000)
    leetcode_hard: int = Field(0, ge=0, le=3000)
    github_url: Optional[str] = None
    linkedin_url: Optional[str] = None

    sql_level: str = "none"
    sql_details: Optional[str] = None

    skills: List[SkillIn] = Field(default_factory=list)
    projects: List[ProjectIn] = Field(default_factory=list)
    internships: List[InternshipIn] = Field(default_factory=list)
    certifications: List[CertificationIn] = Field(default_factory=list)

    resume_filename: Optional[str] = None
    resume_text: Optional[str] = None

    aptitude_self: str = "learning"
    communication_self: str = "learning"

    targets: List[TargetCompanyIn] = Field(default_factory=list, max_length=3)

    @field_validator("sql_level")
    @classmethod
    def _sql_ok(cls, v: str) -> str:
        v = (v or "").strip().lower()
        return v if v in SQL_LEVELS else "none"


class PillarGap(BaseModel):
    pillar: str
    label: str
    have: int
    need: int
    gap: int                # 0-100, how far below the bar (0 = met)
    weight: float
    deficit_points: float   # weighted contribution to the company gap


class TargetGapOut(BaseModel):
    company_slug: str
    company_name: str
    priority: int
    hiring_bar: int
    readiness_pct: int
    gap_pct: int
    verdict: str
    pillar_gaps: List[PillarGap]
    process: List[str] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class CareerProfileOut(BaseModel):
    profile_id: str
    target_domain: str
    profile_score: int
    profile_grade: str
    pillars: Dict[str, int]
    pillar_labels: Dict[str, str]
    fingerprint: str
    targets: List[TargetGapOut]
    has_cached_report: bool = False
    model_config = ConfigDict(from_attributes=True)


class CompanyOut(BaseModel):
    company_slug: str
    company_name: str
    archetype: str
    hiring_bar: int
    focus_notes: Optional[str] = None


class PlanAction(BaseModel):
    action_id: str
    label: str
    route: str
    pillar: str
    why: str
    est_hours: int


class PlanWeek(BaseModel):
    week: int
    theme: str
    actions: List[PlanAction]
    checkpoint: str


class GapReportOut(BaseModel):
    fingerprint: str
    source: str                 # ai | fallback | cache
    profile_score: int
    headline: str
    strengths: List[str]
    critical_gaps: List[str]
    company_notes: Dict[str, str]
    plan: List[PlanWeek]
    generated_at: Optional[str] = None


class ResumeParseOut(BaseModel):
    resume_text: str
    detected_skills: List[str]
    detected_links: Dict[str, str]
    char_count: int
# backend/app/schemas/skillpath_v3.py   [NEW v12]
"""
ATLAS AI 4.0 (v12) — Pydantic v2 schemas for the SkillPath Engine 3.0 surface.
Covers: domain-select cards, per-domain roadmap dashboard, Learn Cards,
subtopic pills, the 25-question practice loop, and multi-domain enrollment.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------- Domain-first navigation ----------
class DomainCard(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    slug: str
    name: str
    pitch: str = ""                     # one-line pitch for the card
    students_on_path: int = 0           # "students on this path" counter
    min_plan_months: int = 3


class EnrollRequest(BaseModel):
    domain_id: str
    plan_id: str


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    domain_id: str
    plan_id: str


class DomainSwitchState(BaseModel):
    enrollments: List[EnrollmentResponse]
    domain_cap: int                     # 1 / 2 / 3 by plan tier
    slots_used: int
    can_add_more: bool


# ---------- Roadmap dashboard (one per domain) ----------
class SubtopicPill(BaseModel):
    subtopic_id: str
    name: str
    status: str = "locked"              # locked | in_progress | mastered
    questions_completed: int = 0        # 0..25
    mastery_score: int = 0              # 0..100


class RoadmapTopicCard(BaseModel):
    topic_id: str
    title: str
    state: str = "grey"                 # grey | blue | green
    is_shared_module: bool = False      # sourced from content_library
    subtopics: List[SubtopicPill] = Field(default_factory=list)


class RoadmapDashboardResponse(BaseModel):
    domain_id: str
    domain_name: str
    plan_months: int
    progress_pct: int = 0               # progress-ring value (pure math)
    topics: List[RoadmapTopicCard] = Field(default_factory=list)


# ---------- Learn Mode (Type A read) ----------
class WorkedExample(BaseModel):
    prompt: str
    solution: str


class LearnCardResponse(BaseModel):
    subtopic_id: str
    name: str
    what_is_it: Optional[str] = None
    when_to_use: Optional[str] = None
    how_to_use: Optional[str] = None
    examples: List[WorkedExample] = Field(default_factory=list)          # exactly 5
    visualization_config: Optional[Dict[str, Any]] = None


# ---------- Practice Mode (25-question loop) ----------
class PracticeQuestionResponse(BaseModel):
    question_id: str
    subtopic_id: str
    position: int                       # 1..25
    of_total: int = 25
    difficulty_tier: str = "basic"      # basic | medium | advanced
    question_kind: str = "text"         # text | code | math | sql
    statement: str
    constraints: Optional[str] = None
    examples: List[WorkedExample] = Field(default_factory=list)          # exactly 2
    source: str = "seed"                # seed | auto (generate-once-cache-forever)


class AttemptRequest(BaseModel):
    question_id: str
    student_answer: str


class AttemptAnalysisResponse(BaseModel):
    verdict: str                        # e.g. "correct" | "partially correct" | "incorrect"
    whats_good: str = ""
    whats_missing: str = ""
    hint: str = ""                      # one nudge toward optimal — never the full answer
    followup: Optional[str] = None      # interview-grade note for Q21-25 only
    score: int = 0                      # 0..10 (used by mastery math, not for points)
    counter: int = 0                    # questions_completed after this attempt (0..25)
    subtopic_status: str = "in_progress"
    can_advance: bool = False           # gates the Next Question button


class RevealRequest(BaseModel):
    question_id: str
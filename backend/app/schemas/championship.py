# championship.py - [NEW] PaperBuild, EnterResponse, AnswerSubmit, ResultView
# backend/app/schemas/championship.py
"""Weekly Championship — request/response schemas (Pydantic v2).

Covers the student exam flow (enter → answer → submit → result), violation
reporting, and the admin console (paper build, schedule, monitor, analysis,
podium, publish).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

# valid state transitions (from → set of allowed targets)
STATE_FLOW: dict[str, set[str]] = {
    "draft":     {"scheduled"},
    "scheduled": {"live"},
    "live":      {"closed"},
    "closed":    {"published"},
    "published": set(),
}
ALL_STATES = list(STATE_FLOW.keys())


# ── question paper format ────────────────────────────────────────────────────
class PaperQuestion(BaseModel):
    """One question inside the 20-question paper."""
    index: int                              # 0–19
    text: str
    kind: str = "mcq"                       # mcq | rapid | math | logic
    options: list[str] = Field(default_factory=list)  # 4 choices for MCQ
    correct: str = ""                       # correct answer key (admin-only)
    points: int = 5                         # per-question marks (default 100 total)


# ── student flow ─────────────────────────────────────────────────────────────
class EnterResponse(BaseModel):
    attempt_id: str
    championship_id: str
    title: str
    questions: list[dict]                   # paper WITHOUT correct answers
    duration_secs: int
    server_deadline: datetime               # entry + duration — the clock that matters
    already_answered: dict = Field(default_factory=dict)


class AnswerSave(BaseModel):
    question_index: int
    answer: str


class SubmitRequest(BaseModel):
    """Client sends its local time_used; server caps at duration_secs."""
    time_used_secs: Optional[int] = None


class ViolationReport(BaseModel):
    """Fullscreen exit / tab-switch event from the client guard."""
    event: str = "fullscreen_exit"          # extensible for future events


class ViolationResponse(BaseModel):
    locked: bool
    fullscreen_exits: int
    message: str


class StudentResult(BaseModel):
    championship_id: str
    title: str
    score: int
    max_score: int
    rank: Optional[int] = None
    total_participants: int = 0
    percentile: Optional[int] = None
    time_used_secs: int = 0
    attention_score: Optional[int] = None
    per_question: list[dict] = Field(default_factory=list)  # {index, your_answer, correct, earned}
    practice_links: list[dict] = Field(default_factory=list)  # {topic, link}
    ai_analysis: Optional[dict] = None
    podium: Optional[dict] = None


# ── admin: paper builder ─────────────────────────────────────────────────────
class PaperBuildRequest(BaseModel):
    """Manual questions + optional AI-draft request."""
    questions: list[PaperQuestion] = Field(default_factory=list)
    ai_draft_count: int = 0                 # ask AI to generate this many extra


class ChampionshipCreate(BaseModel):
    title: str
    college_id: Optional[str] = None        # NULL = platform-wide
    starts_at: datetime
    duration_secs: int = 900
    questions: list[PaperQuestion] = Field(default_factory=list)


class ChampionshipUpdate(BaseModel):
    title: Optional[str] = None
    starts_at: Optional[datetime] = None
    duration_secs: Optional[int] = None
    questions: Optional[list[PaperQuestion]] = None


# ── admin: monitor + results ─────────────────────────────────────────────────
class LiveParticipant(BaseModel):
    user_id: str
    username: str = ""
    entered_at: Optional[datetime] = None
    answers_count: int = 0
    submitted: bool = False
    locked: bool = False
    fullscreen_exits: int = 0


class LiveMonitorResponse(BaseModel):
    championship_id: str
    status: str
    total_entered: int
    total_submitted: int
    total_locked: int
    participants: list[LiveParticipant]


class ResultRow(BaseModel):
    user_id: str
    username: str = ""
    college: str = ""
    score: int = 0
    max_score: int = 100
    time_used_secs: int = 0
    attention_score: Optional[int] = None
    fullscreen_exits: int = 0
    ai_notes: str = ""
    rank: int = 0


class ResultsConsoleResponse(BaseModel):
    championship_id: str
    title: str
    status: str
    results: list[ResultRow]
    podium: Optional[dict] = None


class PodiumSelect(BaseModel):
    first: str                              # user_id
    second: str
    third: str


class AdminChampionshipRow(BaseModel):
    id: str
    title: str
    status: str
    college_id: Optional[str] = None
    starts_at: Optional[datetime] = None
    duration_secs: int = 900
    question_count: int = 0
    participant_count: int = 0
    created_at: Optional[datetime] = None
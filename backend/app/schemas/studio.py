# studio.py - [NEW] StudioSetup, TurnRequest, TurnResponse, FinalReport
# backend/app/schemas/studio.py
"""AI Interview Studio — schemas (Pydantic v2).

PRIVACY BY SCHEMA: every field here is plain text or a number. There is no
field that could carry audio, video, or image data — the API physically cannot
receive media. Presence is a client-computed percentage (0-100), nothing more.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

ALLOWED_LEVELS = ["beginner", "intermediate", "advanced"]
ALLOWED_COUNTS = [3, 10, 15, 20]

# guard against someone smuggling a base64 media blob through a text field
_MAX_TEXT_LEN = 8000


class StudioSetup(BaseModel):
    """Start a session: domain + level + question count."""
    domain: str                              # e.g. "Data Science"
    level: str = "intermediate"              # beginner | intermediate | advanced
    question_count: int = 10                 # 3 | 10 | 15 | 20
    voice_mode: bool = True                  # request TTS audio for questions

    @field_validator("level")
    @classmethod
    def _level_ok(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in ALLOWED_LEVELS:
            raise ValueError(f"level must be one of {ALLOWED_LEVELS}")
        return v

    @field_validator("question_count")
    @classmethod
    def _count_ok(cls, v: int) -> int:
        if v not in ALLOWED_COUNTS:
            raise ValueError(f"question_count must be one of {ALLOWED_COUNTS}")
        return v


class StartResponse(BaseModel):
    session_id: str
    domain: str
    level: str
    question_count: int
    first_question: str
    question_index: int = 0
    audio_b64: Optional[str] = None          # TTS of the first question
    tts_provider: Optional[str] = None       # chatterbox | elevenlabs | None


class TurnRequest(BaseModel):
    """One answered turn: the STT transcript of the student's spoken answer,
    plus optional presence numbers from the on-device camera hook."""
    question_index: int
    transcript_text: str                     # browser Web Speech API output
    presence_pct: Optional[int] = Field(None, ge=0, le=100)
    answer_secs: Optional[int] = Field(None, ge=0)

    @field_validator("transcript_text")
    @classmethod
    def _text_ok(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) > _MAX_TEXT_LEN:
            raise ValueError("transcript too long — text only, no encoded media")
        return v


class TurnResponse(BaseModel):
    question_index: int
    score: int                               # 0-10 for this answer
    feedback: str                            # what was good / what was missing
    model_answer_hint: str = ""
    is_follow_up: bool = False               # next question is a probe, not from the set
    next_question: Optional[str] = None      # None => session complete, call finish
    next_index: Optional[int] = None
    audio_b64: Optional[str] = None          # TTS: feedback + next question
    tts_provider: Optional[str] = None
    session_complete: bool = False


class FinishRequest(BaseModel):
    presence_pct: Optional[int] = Field(None, ge=0, le=100)  # session average


class PlatformPlanItem(BaseModel):
    weakness: str
    feature: str                             # human name, e.g. "DSA Gym"
    link: str                                # real in-platform route
    why: str = ""


class FinalReport(BaseModel):
    session_id: str
    domain: str
    level: str
    questions_answered: int
    overall_score: int                       # 0-100
    presence_pct: Optional[int] = None
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    per_question: list[dict] = Field(default_factory=list)  # {index, question, score}
    improvement_plan: list[PlatformPlanItem] = Field(default_factory=list)
    summary: str = ""
    points_awarded: int = 0


class SessionListItem(BaseModel):
    id: str
    domain: str
    level: str
    question_count: int
    overall_score: Optional[int] = None
    presence_pct: Optional[int] = None
    created_at: Optional[datetime] = None
    finished: bool = False
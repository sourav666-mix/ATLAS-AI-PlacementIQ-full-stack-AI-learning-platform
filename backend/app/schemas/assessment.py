# backend/app/schemas/assessment.py
"""Request/response models for the Assessment Center."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# --- Aptitude ---------------------------------------------------------------
class AptitudeStartIn(BaseModel):
    category: str = Field(examples=["quant", "logical", "verbal", "data_interpretation"])
    level: str = "intermediate"
    count: int = Field(5, ge=1, le=25)


class AptitudeQuestionOut(BaseModel):
    index: int
    question: str
    options: List[str]


class AptitudeStartOut(BaseModel):
    session_id: str
    category: str
    level: str
    questions: List[AptitudeQuestionOut]


class AptitudeSubmitIn(BaseModel):
    answers: List[int]  # selected option index per question (-1 = unanswered)


class AptitudePerQuestion(BaseModel):
    index: int
    selected: int
    correct_index: int
    is_correct: bool
    explanation: Optional[str] = None


class AptitudeResultOut(BaseModel):
    session_id: str
    score: int
    correct_count: int
    total: int
    accuracy: float
    breakdown: List[AptitudePerQuestion]


# --- Mock Interview ---------------------------------------------------------
class MockStartIn(BaseModel):
    role: str
    domain: Optional[str] = None
    level: str = "intermediate"
    count: int = Field(5, ge=1, le=15)


class MockQuestionOut(BaseModel):
    index: int
    question: str


class MockStartOut(BaseModel):
    session_id: str
    role: str
    questions: List[MockQuestionOut]


class MockSubmitIn(BaseModel):
    answers: List[str]


class MockPerQuestion(BaseModel):
    index: int
    question: str
    score: int
    feedback: str


class MockResultOut(BaseModel):
    session_id: str
    overall_score: int
    breakdown: List[MockPerQuestion]
    summary: str


# --- history ----------------------------------------------------------------
class AssessmentHistoryItem(BaseModel):
    id: str
    kind: str          # "aptitude" | "mock"
    label: Optional[str] = None
    score: Optional[int] = None
    completed_at: Optional[datetime] = None


# --- analytics ----------------------------------------------------------------
class AccuracyTrendPoint(BaseModel):
    label: str
    value: float


class WeakestCategory(BaseModel):
    name: str
    accuracy: float


class AssessmentAnalyticsOut(BaseModel):
    aptitude_solved: int       # correctly-answered aptitude questions, lifetime
    mock_sessions: int         # completed mock interview sessions, lifetime
    avg_accuracy: float        # average aptitude accuracy, 0-100
    accuracy_trend: List[AccuracyTrendPoint] = []
    weakest_subtopics: List[WeakestCategory] = []


__all__ = [
    "AptitudeStartIn", "AptitudeQuestionOut", "AptitudeStartOut",
    "AptitudeSubmitIn", "AptitudePerQuestion", "AptitudeResultOut",
    "MockStartIn", "MockQuestionOut", "MockStartOut",
    "MockSubmitIn", "MockPerQuestion", "MockResultOut",
    "AssessmentHistoryItem",
    "AccuracyTrendPoint", "WeakestCategory", "AssessmentAnalyticsOut",
]
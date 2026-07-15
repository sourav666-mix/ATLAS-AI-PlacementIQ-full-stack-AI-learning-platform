# practice.py - AttemptRequest, AttemptResponse, RevealResponse
# backend/app/schemas/practice.py
"""
Request/response models for the practice loop.

QuestionOut deliberately OMITS model_answer and the reveal fields — those are
served only by the explicit /reveal endpoint (still a pure DB read).
"""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    order_index: int
    question_kind: str
    difficulty: str
    question_text: str
    starter_code: Optional[str] = None


class TopicContentOut(BaseModel):
    topic_id: str
    concept_markdown: Optional[str] = None
    examples_json: Optional[list] = None
    questions: List[QuestionOut] = []


class RevealOut(BaseModel):
    question_id: str
    why_explanation: Optional[str] = None
    how_explanation: Optional[str] = None
    example: Optional[str] = None
    common_mistakes: Optional[str] = None


class AttemptIn(BaseModel):
    student_answer: str


class AttemptResultOut(BaseModel):
    score: int
    feedback: str
    attempt_number: int
    is_first_attempt: bool
    mastery_score: int
    topic_completed: bool


__all__ = ["QuestionOut", "TopicContentOut", "RevealOut", "AttemptIn", "AttemptResultOut"]
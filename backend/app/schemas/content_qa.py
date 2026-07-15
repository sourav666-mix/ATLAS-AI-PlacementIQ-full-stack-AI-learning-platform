# backend/app/schemas/content_qa.py
"""
ATLAS AI 4.0 - v12 content pipeline: admin QA schemas.
The review surface for review_status='auto' questions (generate-once-
cache output) and seed coverage - super_admin / college_admin only.
"""

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class CoverageTopic(BaseModel):
    title: str
    subtopics: int
    learn_done: int
    questions_done: int
    questions_target: int
    complete: bool


class CoverageResponse(BaseModel):
    topics: Dict[str, CoverageTopic]
    totals: Dict[str, int]
    auto_pending: int          # auto questions awaiting review


class AutoQuestionRow(BaseModel):
    question_id: str
    topic_title: str
    subtopic_name: str
    difficulty: str
    question_kind: str
    question: str
    model_solution: str
    times_served: int           # attempts recorded against it


class AutoQuestionListResponse(BaseModel):
    questions: List[AutoQuestionRow]
    total_pending: int


class ReviewRequest(BaseModel):
    action: Literal["approve", "reject"]
    note: Optional[str] = Field(default=None, max_length=500)


class ReviewResponse(BaseModel):
    question_id: str
    new_status: str             # published | rejected
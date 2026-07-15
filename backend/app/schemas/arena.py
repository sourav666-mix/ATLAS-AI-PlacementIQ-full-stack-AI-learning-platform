# arena.py - [NEW] ProblemResponse, RunRequest, SubmitRequest, ReviewResponse
# backend/app/schemas/arena.py
"""Request/response models for Code Arena Pro."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ProblemSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    category: str
    difficulty: str
    title: Optional[str] = None
    topic: Optional[str] = None
    pattern_tag: Optional[str] = None


class ProblemDetail(BaseModel):
    id: str
    category: str
    difficulty: str
    title: Optional[str] = None
    topic: Optional[str] = None
    pattern_tag: Optional[str] = None
    statement: Optional[str] = None
    examples: List[dict] = []
    constraints: List = []
    hints: List = []
    starter_code: dict = {}
    visible_tests: List[dict] = []


class SubmitIn(BaseModel):
    language: str = "python"
    code: str


class RunIn(BaseModel):
    problem_id: str
    language: str = "python"
    code: str


class TestResult(BaseModel):
    index: int
    passed: bool
    error: Optional[str] = None


class SubmitResult(BaseModel):
    passed: bool
    tests_passed: int
    total_tests: int
    visible_results: List[TestResult]
    runtime_ms: int
    points_awarded: int
    ai_review: dict
    compile_error: Optional[str] = None


__all__ = ["ProblemSummary", "ProblemDetail", "SubmitIn", "RunIn", "TestResult", "SubmitResult"]
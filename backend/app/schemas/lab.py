# FILE: app/schemas/lab.py
# BATCH 20 / v11 Phase 13 (new) - Pydantic v2 schemas for the Live Lab
# surface: LabResponse, GradeResult, CopilotRequest, ColabLaunch,
# CompleteRequest (names per the v11 folder structure doc).

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------
class LabListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    lab_type: str
    needs_gpu: bool = False
    dataset_ref: Optional[str] = None


class LabResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    lab_type: str
    starter_code: Optional[str] = None
    dataset_ref: Optional[str] = None
    graded_tasks: List[Dict[str, Any]] = Field(default_factory=list)
    needs_gpu: bool = False
    dataset: Optional[Dict[str, Any]] = None      # resolved lab_datasets row
    session: Optional[Dict[str, Any]] = None      # the student's session


# ---------------------------------------------------------------------------
# Grading — NO AI; the browser ran the hidden tests, we record the results
# ---------------------------------------------------------------------------
class ArtifactMeta(BaseModel):
    name: str = Field(..., max_length=200)
    size_kb: int = Field(..., ge=0, le=1_000_000)
    kind: Optional[str] = Field(default=None, max_length=40)


class GradeRequest(BaseModel):
    lab_id: str
    tasks_passed: Dict[str, bool]
    code_snapshot: Optional[str] = Field(default=None, max_length=200_000)
    artifacts: Optional[List[ArtifactMeta]] = None


class GradeResult(BaseModel):
    lab_id: str
    passed: int
    total: int
    all_passed: bool
    status: str


# ---------------------------------------------------------------------------
# Copilot — bounded Type-B (explain / suggest / fix / review)
# ---------------------------------------------------------------------------
class CopilotRequest(BaseModel):
    lab_id: str
    code: Optional[str] = Field(default=None, max_length=20_000)
    error: Optional[str] = Field(default=None, max_length=4_000)
    question: Optional[str] = Field(default=None, max_length=1_000)
    dataset_shape: Optional[str] = Field(default=None, max_length=500)


class CopilotResponse(BaseModel):
    mode: str
    answer: str
    cached: bool = False
    calls_left_today: Optional[int] = None


# ---------------------------------------------------------------------------
# Colab bridge + completion
# ---------------------------------------------------------------------------
class ColabLaunch(BaseModel):
    lab_id: str
    code: Optional[str] = Field(default=None, max_length=200_000)


class ColabLaunchResponse(BaseModel):
    filename: str
    notebook: Dict[str, Any]
    open_url: str
    note: str


class CompleteRequest(BaseModel):
    lab_id: str
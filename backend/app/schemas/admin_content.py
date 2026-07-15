# FILE: app/schemas/admin_content.py
# BATCH 16 (new) - Schemas for the admin content / analytics / providers surface.
# NOTE: This is a NEW file so app/schemas/admin.py (Batch 15) stays untouched.

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Flexible payloads: curriculum tables (domains / domain_phases / roadmap_topics
# / topic_content / topic_questions / arena_problems) accept any subset of their
# real columns. The service layer applies ONLY keys that are actual columns
# (apply_fields), so unknown keys are safely ignored.
# ---------------------------------------------------------------------------
class RowPayload(BaseModel):
    """Open payload — pass any column of the target table."""
    model_config = ConfigDict(extra="allow")


class ReorderItem(BaseModel):
    id: str
    sort_order: int


class ReorderRequest(BaseModel):
    items: List[ReorderItem] = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Questions: draft -> publish workflow
# ---------------------------------------------------------------------------
class QuestionStatusAction(BaseModel):
    ids: List[str] = Field(..., min_length=1)
    action: str = Field(..., pattern="^(publish|draft|flag)$")


class RegenerateRequest(BaseModel):
    instructions: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional admin guidance, e.g. 'make it harder, focus on edge cases'",
    )


# ---------------------------------------------------------------------------
# Arena QA queue ('auto' generated problems)
# ---------------------------------------------------------------------------
class ArenaReviewAction(BaseModel):
    action: str = Field(..., pattern="^(publish|flag|draft)$")


# ---------------------------------------------------------------------------
# Providers
# ---------------------------------------------------------------------------
class ProviderToggleResponse(BaseModel):
    provider: str
    enabled: bool
    note: Optional[str] = None
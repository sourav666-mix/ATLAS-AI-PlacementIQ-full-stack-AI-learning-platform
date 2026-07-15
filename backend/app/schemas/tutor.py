# backend/app/schemas/tutor.py
"""Request/response models for the Global AI Assistant."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class TutorAskIn(BaseModel):
    message: str
    source_page: Optional[str] = None


class TutorReplyOut(BaseModel):
    response: str
    context_used: dict


class TutorHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    message: str
    response: Optional[str] = None
    source_page: Optional[str] = None
    created_at: datetime


__all__ = ["TutorAskIn", "TutorReplyOut", "TutorHistoryOut"]
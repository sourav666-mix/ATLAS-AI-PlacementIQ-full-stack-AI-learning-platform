# backend/app/schemas/progress.py
"""Response models for the progress / scoring endpoints."""
from datetime import date
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class RadarScoreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    skill_category: str
    score: int


class DailyActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    activity_date: date
    questions_attempted: int
    avg_score: float
    topics_completed: int
    arena_points: int
    interview_points: int
    championship_points: int
    daily_points: int
    streak_days: int


class ProgressSummary(BaseModel):
    profile_bar_score: int
    streak_days: int
    today_points: int
    today: Optional[DailyActivityOut] = None
    radar: List[RadarScoreOut] = []


__all__ = ["RadarScoreOut", "DailyActivityOut", "ProgressSummary"]
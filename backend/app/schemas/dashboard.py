# FILE: app/schemas/dashboard.py
# BATCH 17 (new) - Response schemas for the dashboard + nudge endpoints.
# Loose typing on nested payloads (dicts) — the service assembles them
# defensively, matching the pattern used across Batches 11-16.

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class DailyRing(BaseModel):
    points_today: int
    goal: int
    pct: int


class StreakInfo(BaseModel):
    days: int
    next_milestone: Optional[int] = None


class NextAction(BaseModel):
    component: str
    message: str


class ProfileBar(BaseModel):
    score: int
    components: Dict[str, int]
    weights: Dict[str, int]
    what_raises_this_next: NextAction


class Nudge(BaseModel):
    date: str
    kind: str
    message: str
    link: Optional[str] = None


class DashboardResponse(BaseModel):
    daily_ring: DailyRing
    streak: StreakInfo
    radar: List[Dict[str, Any]]
    profile_bar: ProfileBar
    modules: Dict[str, int]
    nudge: Optional[Nudge] = None
    generated_at: str


class NudgeResponse(BaseModel):
    nudge: Optional[Nudge] = None
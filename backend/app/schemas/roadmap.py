# roadmap.py - [MOD] RoadmapGenerateRequest, RoadmapResponse, SubtopicNode
# backend/app/schemas/roadmap.py
"""Request/response models for subscribing and viewing the roadmap."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class SubscribeIn(BaseModel):
    plan_slug: str
    domain_slug: str


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    plan_id: str
    domain_id: str
    plan_months: int
    status: str
    started_at: datetime
    expires_at: Optional[datetime] = None
    roadmap_generated: bool


class RoadmapItemOut(BaseModel):
    topic_id: str
    title: str
    slug: str
    skill_category: Optional[str] = None
    phase_name: str
    order_index: int
    status: str
    mastery_score: int
    questions_completed: int


class RoadmapOut(BaseModel):
    subscription: SubscriptionOut
    items: List[RoadmapItemOut] = []


__all__ = ["SubscribeIn", "SubscriptionOut", "RoadmapItemOut", "RoadmapOut"]
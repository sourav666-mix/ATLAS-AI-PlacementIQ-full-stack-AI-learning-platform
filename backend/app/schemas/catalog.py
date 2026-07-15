# backend/app/schemas/catalog.py
"""Response models for the public catalogue: domains, phases, topics, plans."""
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    slug: str
    plan_months: int
    price_inr: int
    description: Optional[str] = None
    features_json: Optional[dict] = None


class DomainOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    slug: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    order_index: int


class PhaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    min_plan_months: int
    order_index: int


class TopicOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    title: str
    slug: str
    skill_category: Optional[str] = None
    order_index: int
    parent_topic_id: Optional[str] = None
    phase_id: str


class DomainDetailOut(DomainOut):
    phases: List[PhaseOut] = []
    topics: List[TopicOut] = []


__all__ = ["PlanOut", "DomainOut", "PhaseOut", "TopicOut", "DomainDetailOut"]
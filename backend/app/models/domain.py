# backend/app/models/domain.py
"""
Curriculum skeleton (SHARED across all students — written once, read forever).

domains ........... 7 fixed career tracks (data_science, software_engineer, ...)
domain_phases ..... Foundation / Core / Advanced / Capstone, each tagged with
                    min_plan_months (3 / 3 / 6 / 9) — the roadmap filter key.
roadmap_topics .... ordered topics; parent_topic_id builds the subtopic tree
                    (NULL parent = top-level topic; set parent = a subtopic).

This is Type-A data. Assigning it to a student is a pure SQL filter (no AI).
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.plan import UserSubscription


def _uuid() -> str:
    return str(uuid.uuid4())


class Domain(Base):
    __tablename__ = "domains"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)  # data_science
    name: Mapped[str] = mapped_column(String(120), nullable=False)                          # "Data Science"
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # --- relationships ------------------------------------------------------
    phases: Mapped[list["DomainPhase"]] = relationship(
        back_populates="domain",
        cascade="all, delete-orphan",
        order_by="DomainPhase.order_index",
    )
    topics: Mapped[list["RoadmapTopic"]] = relationship(
        back_populates="domain",
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[list["UserSubscription"]] = relationship(
        back_populates="domain"
    )

    def __repr__(self) -> str:
        return f"<Domain {self.slug}>"


class DomainPhase(Base):
    __tablename__ = "domain_phases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    domain_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("domains.id", ondelete="CASCADE"), index=True, nullable=False
    )

    name: Mapped[str] = mapped_column(String(60), nullable=False)      # Foundation | Core | Advanced | Capstone
    # The roadmap filter key: a phase unlocks if min_plan_months <= plan_months.
    min_plan_months: Mapped[int] = mapped_column(Integer, nullable=False)  # 3 | 6 | 9
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    domain: Mapped["Domain"] = relationship(back_populates="phases")
    topics: Mapped[list["RoadmapTopic"]] = relationship(
        back_populates="phase",
        cascade="all, delete-orphan",
        order_by="RoadmapTopic.order_index",
    )

    def __repr__(self) -> str:
        return f"<DomainPhase {self.name} (>= {self.min_plan_months}m)>"


class RoadmapTopic(Base):
    __tablename__ = "roadmap_topics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # v12: NULLable — shared-library topics carry no domain.
    domain_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("domains.id", ondelete="CASCADE"), index=True, nullable=True
    )
    # v12: NULLable — shared-library topics carry no single phase (phase is
    # per-domain now, via DomainRoadmapItem.phase).
    phase_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("domain_phases.id", ondelete="CASCADE"), index=True, nullable=True
    )
    # v10 subtopic tree: NULL = top-level topic; set = a subtopic of another topic.
    parent_topic_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("roadmap_topics.id", ondelete="CASCADE"), index=True, nullable=True
    )

    title: Mapped[str] = mapped_column(String(150), nullable=False)      # "Loops"
    slug: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    skill_category: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)  # feeds skill radar
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    item_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    estimated_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # --- v12 Learn Mode (Type A) --------------------------------------------
    what_is_it: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # concept: what it is
    when_to_use: Mapped[Optional[str]] = mapped_column(Text, nullable=True)     # concept: when to reach for it
    how_to_use: Mapped[Optional[str]] = mapped_column(Text, nullable=True)      # concept: how to use it
    examples_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # EXACTLY 5 worked examples
    visualization_config_json: Mapped[Optional[dict]] = mapped_column(          # {"type": "...", "params": [...]}
        JSON, nullable=True
    )

    # --- relationships ------------------------------------------------------
    domain: Mapped[Optional["Domain"]] = relationship(back_populates="topics")
    phase: Mapped[Optional["DomainPhase"]] = relationship(back_populates="topics")
    subtopics: Mapped[list["RoadmapTopic"]] = relationship(
        back_populates="parent",
        cascade="all, delete-orphan",
        order_by="RoadmapTopic.order_index",
    )
    parent: Mapped[Optional["RoadmapTopic"]] = relationship(
        back_populates="subtopics",
        remote_side="RoadmapTopic.id",
    )

    def __repr__(self) -> str:
        kind = "subtopic" if self.parent_topic_id else "topic"
        return f"<RoadmapTopic {kind} {self.slug}>"
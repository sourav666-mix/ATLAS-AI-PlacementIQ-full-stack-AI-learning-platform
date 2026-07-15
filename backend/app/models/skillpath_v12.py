# backend/app/models/skillpath_v12.py
"""
ATLAS AI 4.0 - v12 SkillPath Reforged: shared-library roadmap model.

v12 schema delta (locked, Section 5 of the v12 spec):
  * NEW table  domain_roadmap_items  - a domain's roadmap references shared
    library topics by ID, with a per-domain order and phase mapping.
  * ALTER      user_topic_progress   - + domain_id (nullable) so a student's
    Python progress in Data Science never leaks into Backend Developer.
    (One-line additive snippet for models/skill_progress.py ships in
     V12_BATCH1_SNIPPETS.md - this file adds ONLY the new table.)

Content is shared; progress is always per-student-per-domain.
"""

import uuid

from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class DomainRoadmapItem(Base):
    """One ordered entry in a domain's roadmap, pointing into the shared
    topic library (roadmap_topics). Seeded once by scripts/seed_content.py
    from services/curriculum_registry.py - never written at request time."""

    __tablename__ = "domain_roadmap_items"

    id = Column(String(36), primary_key=True, default=_uuid)
    domain_id = Column(
        String(36),
        ForeignKey("domains.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    topic_id = Column(
        String(36),
        ForeignKey("roadmap_topics.id"),
        nullable=False,
        index=True,
    )
    item_order = Column(Integer, nullable=False)
    # Foundation / Core / Advanced - drives the plan gate (3 / 3 / 6 months)
    phase = Column(String(20), nullable=False, default="Core")
    # deterministic estimate shown on the roadmap card (hours)
    est_hours = Column(Integer, nullable=False, default=6)

    domain = relationship("Domain", lazy="noload")
    topic = relationship("RoadmapTopic", lazy="noload")

    __table_args__ = (
        UniqueConstraint("domain_id", "topic_id", name="uq_domain_topic"),
        UniqueConstraint("domain_id", "item_order", name="uq_domain_order"),
        Index("ix_dri_domain_order", "domain_id", "item_order"),
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<DomainRoadmapItem domain={self.domain_id} "
            f"topic={self.topic_id} order={self.item_order} phase={self.phase}>"
        )

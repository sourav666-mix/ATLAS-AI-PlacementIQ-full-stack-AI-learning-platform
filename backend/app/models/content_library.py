# backend/app/models/content_library.py   [NEW v12]
"""
ATLAS AI 4.0 (v12) — Shared Content Library (the de-duplication layer).

content_library   : the 5 shared modules (python, numpy, pandas, dataviz, stats_linalg)
                    authored ONCE, read by every domain that maps them.
domain_topic_map  : which domain shows which shared module, and in what display order.

Type A only. Edit one row here -> it reflects on every mapped domain roadmap with no re-seed.
Nothing in this file ever calls a live AI provider.
"""
import uuid
from sqlalchemy import Column, String, Integer, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ContentLibrary(Base):
    __tablename__ = "content_library"

    id = Column(String(36), primary_key=True, default=_uuid)
    module_key = Column(String(60), unique=True, nullable=False)  # 'python','numpy','pandas','dataviz','stats_linalg'
    title = Column(String(150), nullable=False)
    subtopics_json = Column(JSON, nullable=True)  # [{"name": "...", "order": 1}, ...]

    mappings = relationship(
        "DomainTopicMap",
        back_populates="content_module",
        cascade="all, delete-orphan",
    )


class DomainTopicMap(Base):
    __tablename__ = "domain_topic_map"
    __table_args__ = (
        # a shared module maps at most once into a given domain (idempotent seeding)
        UniqueConstraint("domain_id", "content_module_id", name="uq_domain_module"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    domain_id = Column(String(36), ForeignKey("domains.id"), nullable=False)
    content_module_id = Column(String(36), ForeignKey("content_library.id"), nullable=False)
    display_order = Column(Integer, nullable=False, default=1)

    content_module = relationship("ContentLibrary", back_populates="mappings")
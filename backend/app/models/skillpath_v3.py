# backend/app/models/skillpath_v3.py   [NEW v12]
"""
ATLAS AI 4.0 (v12) — per-student SkillPath progress + multi-domain enrollment.

subtopic_progress  : per-student, per-subtopic mastery. Drives the pill colour
                     (locked | in_progress | mastered) and the 25-question counter.
domain_enrollments : multi-domain enrollment, capped by plan tier
                     (3-mo = 1 domain, 6-mo = 2, 9-mo = 3).

Pure per-student data. Every value here is written by deterministic math
(practice_engine + progress_engine) — never by a live AI call.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, UniqueConstraint

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class SubtopicProgress(Base):
    __tablename__ = "subtopic_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "subtopic_id", name="uq_user_subtopic"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subtopic_id = Column(String(36), nullable=False)   # -> roadmap_topics.id (a subtopic row)
    questions_completed = Column(Integer, default=0)   # 0..25 (first-attempt only)
    mastery_score = Column(Integer, default=0)         # 0..100
    status = Column(String(12), default="locked")      # locked | in_progress | mastered


class DomainEnrollment(Base):
    __tablename__ = "domain_enrollments"
    __table_args__ = (
        UniqueConstraint("user_id", "domain_id", name="uq_user_domain"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    domain_id = Column(String(36), ForeignKey("domains.id"), nullable=False)
    plan_id = Column(String(36), nullable=False)       # -> subscription plan / user_subscriptions
    enrolled_at = Column(DateTime, default=datetime.utcnow)
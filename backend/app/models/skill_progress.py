# backend/app/models/skill_progress.py
"""
Per-student progress + the skill radar feed.

user_topic_progress .. one row per assigned topic (status + mastery_score).
                       Created in bulk by generate_roadmap() at subscribe time.
skill_radar_scores ... aggregated 0-100 score per skill category (radar chart).

Both are pure per-student data, updated by progress_engine.py (pure math).
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import User

def _uuid() -> str:
    return str(uuid.uuid4())


class UserTopicProgress(Base):
    __tablename__ = "user_topic_progress"
    __table_args__ = (
        # v12: one row per user+topic+domain (a shared-library topic can be
        # reused across domains; progress is tracked separately per domain).
        UniqueConstraint("user_id", "topic_id", "domain_id", name="uq_user_topic_domain"),
    )
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    domain_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)  # v12: per-domain progress
    progress_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # v12: {_seen_qids,_answered,_correct,_score_sum}
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    topic_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roadmap_topics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    subscription_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("user_subscriptions.id", ondelete="CASCADE"), nullable=True
    )

    status: Mapped[str] = mapped_column(String(15), default="not_started", nullable=False)  # not_started|current|completed
    mastery_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)          # 0-100
    questions_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    user: Mapped["User"] = relationship()          # noqa: F821
    topic: Mapped["RoadmapTopic"] = relationship() # noqa: F821

    def __repr__(self) -> str:
        return f"<UserTopicProgress user={self.user_id} topic={self.topic_id} {self.status}>"


class SkillRadarScore(Base):
    __tablename__ = "skill_radar_scores"
    __table_args__ = (
        UniqueConstraint("user_id", "skill_category", name="uq_user_skill"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    skill_category: Mapped[str] = mapped_column(String(80), nullable=False)  # "Python", "ML", "Interview", ...
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)   # 0-100

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True
    )

    user: Mapped["User"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<SkillRadarScore user={self.user_id} {self.skill_category}={self.score}>"
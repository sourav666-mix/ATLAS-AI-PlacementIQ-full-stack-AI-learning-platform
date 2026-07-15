# backend/app/models/daily_activity.py
"""
daily_activity — one row per student per calendar day.

This is the raw material the Scoring Spine works on. progress_engine.record_event()
updates today's row; daily_points is recomputed by the pure-math formula:

    daily_points = questions_attempted*2 + avg_score*1.5 + topics_completed*15
                 + arena_points + interview_points + championship_points
                 + min(streak_days,10)*2

Streak rule: +1 once per calendar day with >=1 attempt; RESETS TO 1 after a gap.
"""
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import User

def _uuid() -> str:
    return str(uuid.uuid4())


class DailyActivity(Base):
    __tablename__ = "daily_activity"
    __table_args__ = (
        UniqueConstraint("user_id", "activity_date", name="uq_user_day"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    activity_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)

    questions_attempted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    topics_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    arena_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    interview_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    championship_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    daily_points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    streak_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    user: Mapped["User"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<DailyActivity user={self.user_id} {self.activity_date} pts={self.daily_points}>"
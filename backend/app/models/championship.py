# backend/app/models/championship.py
"""
Weekly Championship (proctored, one attempt per student — DB-enforced).

championships ......... the event: 20-question paper, 15-min window, status flow.
championship_attempts . one attempt per student; proctor signals (fullscreen_exits,
                        attention_score) and a `locked` flag (1 = violated, no re-entry).
                        ai_analysis_json is filled later by the batch job.

The uq_champ_user unique key is the hard guarantee of "one attempt only".
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:  # imported only for type checkers, not at runtime
    from app.models.user import User


def _uuid() -> str:
    return str(uuid.uuid4())


class Championship(Base):
    __tablename__ = "championships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    college_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)  # NULL = platform-wide

    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_secs: Mapped[int] = mapped_column(Integer, default=900, nullable=False)          # 15 minutes

    question_paper_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)  # 20 questions
    status: Mapped[str] = mapped_column(String(12), default="draft", nullable=False)  # draft|scheduled|live|closed|published
    podium_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)          # admin-selected 1st/2nd/3rd

    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)      # admin_users.id (soft link)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    attempts: Mapped[list["ChampionshipAttempt"]] = relationship(
        back_populates="championship", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Championship {self.title!r} {self.status}>"


class ChampionshipAttempt(Base):
    __tablename__ = "championship_attempts"
    __table_args__ = (
        UniqueConstraint("championship_id", "user_id", name="uq_champ_user"),  # one attempt only
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    championship_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("championships.id", ondelete="CASCADE"), index=True, nullable=False
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    answers_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    time_used_secs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    fullscreen_exits: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    attention_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # True = exited/violated

    ai_analysis_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # filled by batch job
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    championship: Mapped["Championship"] = relationship(back_populates="attempts")
    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<ChampionshipAttempt champ={self.championship_id} user={self.user_id} score={self.score}>"
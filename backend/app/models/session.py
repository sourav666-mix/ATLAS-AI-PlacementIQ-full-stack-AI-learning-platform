# backend/app/models/session.py
"""
Assessment Center persistence.

mock_sessions ...... one row per Mock Interview Pro run.
aptitude_sessions .. one row per Aptitude Pro set.

Both are per-student. Generation/evaluation happens in assessment_service.py
(a Type-B live-AI surface); this file only stores the results + analytics feed.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

from app.models.user import User
def _uuid() -> str:
    return str(uuid.uuid4())


class MockSession(Base):
    __tablename__ = "mock_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    role: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)   # target role
    domain: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    level: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)   # easy|intermediate|hard

    questions_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    answers_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    per_question_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    overall_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(15), default="in_progress", nullable=False)  # in_progress|completed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<MockSession user={self.user_id} score={self.overall_score}>"


class AptitudeSession(Base):
    __tablename__ = "aptitude_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    category: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)  # quant|logical|verbal|data_interp
    level: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)

    total_questions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    correct_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    accuracy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    questions_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    answers_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    time_taken_secs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    status: Mapped[str] = mapped_column(String(15), default="in_progress", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<AptitudeSession user={self.user_id} {self.correct_count}/{self.total_questions}>"
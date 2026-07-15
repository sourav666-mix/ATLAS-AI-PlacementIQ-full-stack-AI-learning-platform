# interview_studio.py - [NEW] InterviewStudioSession (text-only storage)
# backend/app/models/interview_studio.py
"""
AI Interview Studio — voice mock-interview session (numbers only, no media stored).

interview_studio_sessions .. one row per session. Only text transcript + computed
scores are persisted; NO audio and NO video are ever stored (presence_pct is
client-computed). report_json holds strengths/weaknesses/platform plan.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:  # imported only for type checkers, not at runtime
    from app.models.user import User


def _uuid() -> str:
    return str(uuid.uuid4())


class InterviewStudioSession(Base):
    __tablename__ = "interview_studio_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    domain: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    level: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    question_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    transcript_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)          # Q/A text turns only
    per_question_scores_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    overall_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    presence_pct: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)           # client-computed number
    report_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<InterviewStudioSession user={self.user_id} score={self.overall_score}>"
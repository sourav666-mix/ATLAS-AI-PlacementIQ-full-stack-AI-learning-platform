# resume_doc.py - [NEW] ResumeDocument (analyzer + builder outputs)
# backend/app/models/resume_doc.py
"""
Resume AI 2.0 — analyzer + builder output.

resume_documents .. one row per analyzed or built resume.
    mode='analyzed' -> source_file + jd_text + analysis_json (ATS, match, STAR,
                       top-3 predicted questions).
    mode='built'    -> resume_json (structured content) + template + pdf_url.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:  # imported only for type checkers, not at runtime
    from app.models.user import User

LongText = Text().with_variant(LONGTEXT(), "mysql")


def _uuid() -> str:
    return str(uuid.uuid4())


class ResumeDocument(Base):
    __tablename__ = "resume_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    mode: Mapped[str] = mapped_column(String(10), nullable=False)  # analyzed|built

    source_file: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    jd_text: Mapped[Optional[str]] = mapped_column(LongText, nullable=True)

    analysis_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # ATS, match, STAR, top-3 Qs
    resume_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)    # structured builder content

    template: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # classic_ats|modern_minimal|technical_compact
    pages: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    pdf_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship()

    def __repr__(self) -> str:
        return f"<ResumeDocument user={self.user_id} mode={self.mode}>"
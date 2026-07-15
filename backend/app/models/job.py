# backend/app/models/job.py
"""
Verified Jobs & Internships Board.

job_postings .. created by an admin. college_id NULL = platform-wide (super admin);
                set = college-only. visibility controls student reach.
job_tracking .. one row per (student, job): their pipeline stage + match score.
                match_score is computed by jobs_service via embeddings (NO LLM).
"""
import uuid
from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:  # imported only for type checkers, not at runtime
    from app.models.user import User
    from app.models.admin_user import AdminUser

LongText = Text().with_variant(LONGTEXT(), "mysql")


def _uuid() -> str:
    return str(uuid.uuid4())


class JobPosting(Base):
    __tablename__ = "job_postings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    posted_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("admin_users.id"), index=True, nullable=False
    )
    college_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)  # NULL = platform-wide

    visibility: Mapped[str] = mapped_column(String(12), default="all", nullable=False)  # all|college_only
    kind: Mapped[str] = mapped_column(String(12), nullable=False)                       # job|internship

    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    work_mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)         # onsite|remote|hybrid
    ctc_band: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    stipend: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)

    required_skills_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    eligibility_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(LongText, nullable=True)
    apply_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    deadline: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(12), default="active", nullable=False)   # active|closed

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    posted_by_admin: Mapped["AdminUser"] = relationship()
    tracking: Mapped[list["JobTracking"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<JobPosting {self.kind} {self.title!r} @ {self.company!r}>"


class JobTracking(Base):
    __tablename__ = "job_tracking"
    __table_args__ = (
        UniqueConstraint("user_id", "job_id", name="uq_user_job"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    job_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_postings.id", ondelete="CASCADE"), index=True, nullable=False
    )

    stage: Mapped[str] = mapped_column(String(20), default="saved", nullable=False)  # saved|applied|test|interview|offer|rejected
    match_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=True
    )

    user: Mapped["User"] = relationship()
    job: Mapped["JobPosting"] = relationship(back_populates="tracking")

    def __repr__(self) -> str:
        return f"<JobTracking user={self.user_id} job={self.job_id} {self.stage}>"
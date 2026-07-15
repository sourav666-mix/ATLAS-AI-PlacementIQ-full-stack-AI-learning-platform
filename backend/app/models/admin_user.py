# backend/app/models/admin_user.py
"""
admin_users — separate credential space for the admin panel (isolated from students).

role:
    super_admin   -> full platform control (content, revenue, all colleges/students)
    college_admin -> scoped to their college_id (own cohort + own postings only)
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class AdminUser(Base):
    __tablename__ = "admin_users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    role: Mapped[str] = mapped_column(String(20), default="college_admin", nullable=False)  # super_admin|college_admin
    college_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("colleges.id", ondelete="SET NULL"), index=True, nullable=True
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    college: Mapped[Optional["College"]] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<AdminUser {self.email} ({self.role})>"
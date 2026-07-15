# backend/app/models/college.py
"""
colleges — B2B tenant with license seats and contract dates.

A college_admin (admin_users.role='college_admin') is scoped to their college_id.
Students carry a nullable users.college_id linking them to their cohort.

created_by is a plain nullable String (no hard FK) to avoid a circular FK with
admin_users; the relationship is enforced at the service layer.
"""
import uuid
from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class College(Base):
    __tablename__ = "colleges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    license_seats: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    seats_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    contract_start: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    contract_end: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(12), default="active", nullable=False)  # active|expired|trial

    created_by: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)  # admin_users.id (soft link)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return f"<College {self.slug} seats={self.seats_used}/{self.license_seats}>"
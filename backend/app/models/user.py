# user.py - [MOD] User (+ profile_bar_score), PlacementProfile
# backend/app/models/user.py
"""
User + PlacementProfile models.

users .................. one row per student (auth + profile_bar_score, v10)
placement_profiles ..... one optional row per student (career targets)

profile_bar_score is the 0-100 composite maintained by progress_engine.py.
college_id links a student to a B2B college cohort; it is nullable
(NULL = a direct/individual student). The formal FK to colleges(id) is added
in the migration once the College model exists.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    # v10: 0-100 composite kept in sync by progress_engine.py
    profile_bar_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # B2B cohort link (nullable; FK added with the College model / migration)
    college_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    # --- relationships ------------------------------------------------------
    profile: Mapped[Optional["PlacementProfile"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    subscriptions: Mapped[list["UserSubscription"]] = relationship(  # noqa: F821
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class PlacementProfile(Base):
    __tablename__ = "placement_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    college_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    degree: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    graduation_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cgpa: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    target_role: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    target_companies: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    user: Mapped["User"] = relationship(back_populates="profile")

    def __repr__(self) -> str:
        return f"<PlacementProfile user={self.user_id}>"
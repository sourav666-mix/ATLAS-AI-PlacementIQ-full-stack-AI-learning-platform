# backend/app/models/plan.py
"""
Subscription models.

subscription_plans .... shared catalogue (3 / 6 / 9-month tiers). Written once.
user_subscriptions .... one row per student subscription (domain + plan + dates).

Roadmap generation reads plan_months here to filter domain_phases
(min_plan_months <= plan_months). See roadmap_service.py (later batch).
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import User

def _uuid() -> str:
    return str(uuid.uuid4())


class SubscriptionPlan(Base):
    __tablename__ = "subscription_plans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    name: Mapped[str] = mapped_column(String(100), nullable=False)   # "6-Month Career Track"
    slug: Mapped[str] = mapped_column(String(60), unique=True, index=True, nullable=False)
    plan_months: Mapped[int] = mapped_column(Integer, nullable=False)  # 3 | 6 | 9
    price_inr: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    features_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    subscriptions: Mapped[list["UserSubscription"]] = relationship(
        back_populates="plan"
    )

    def __repr__(self) -> str:
        return f"<SubscriptionPlan {self.slug} ({self.plan_months}m)>"


class UserSubscription(Base):
    __tablename__ = "user_subscriptions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    plan_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("subscription_plans.id"), nullable=False
    )
    domain_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("domains.id"), nullable=False
    )

    # Denormalised for fast roadmap filtering / display.
    plan_months: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(12), default="active", nullable=False)  # active|expired|cancelled

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # True once generate_roadmap() has run (guarantees it runs only once).
    roadmap_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # --- relationships ------------------------------------------------------
    user: Mapped["User"] = relationship(back_populates="subscriptions")            # noqa: F821
    plan: Mapped["SubscriptionPlan"] = relationship(back_populates="subscriptions")
    domain: Mapped["Domain"] = relationship(back_populates="subscriptions")        # noqa: F821

    def __repr__(self) -> str:
        return f"<UserSubscription user={self.user_id} domain={self.domain_id}>"
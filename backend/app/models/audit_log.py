# backend/app/models/audit_log.py
"""
audit_log — every admin write goes through audit_service.log_admin_action().

Immutable trail: who did what, to which entity, with what payload, from where.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.admin_user import AdminUser


def _uuid() -> str:
    return str(uuid.uuid4())


class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    admin_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("admin_users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    action: Mapped[str] = mapped_column(String(80), nullable=False)          # e.g. "create_topic"
    entity_type: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)  # "roadmap_topic"
    entity_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    details_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    admin: Mapped["AdminUser"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<AuditLog admin={self.admin_id} {self.action}>"
# backend/app/models/company_intel.py
"""
Company Intel Pro — cache-first report store.

company_intel_cache .. one row per company_slug. company_intel_service checks
this table first; only on a miss (or past expires_at) does it call AI, then
writes the fresh report_json back here. Pure cost-control table.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class CompanyIntelCache(Base):
    __tablename__ = "company_intel_cache"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    company_slug: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)
    report_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    generated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<CompanyIntelCache {self.company_slug}>"
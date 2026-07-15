# backend/app/models/tutor_history.py
"""
tutor_history — the Global AI Assistant chat log (the ONLY table the assistant
writes to).

The assistant has NO memory. Every message is answered by injecting a freshly
assembled context snapshot into the prompt (tutor_context_service.assemble_context).
We store that snapshot per turn for debugging/analytics, plus which page the
student asked from.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import User

def _uuid() -> str:
    return str(uuid.uuid4())


class TutorHistory(Base):
    __tablename__ = "tutor_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)          # student's message
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # assistant reply

    # v9/v10 context columns:
    context_snapshot: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    source_page: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<TutorHistory user={self.user_id} page={self.source_page}>"
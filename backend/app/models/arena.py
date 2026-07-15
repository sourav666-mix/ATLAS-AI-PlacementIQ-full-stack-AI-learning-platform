# backend/app/models/arena.py
"""
Code Arena Pro / DSA Gym — hybrid problem bank (generate-once, cache-forever).

arena_problems ..... shared problem bank. source='seed' (pre-built) or 'auto'
                     (live-generated ONCE by arena_service, then cached here).
arena_submissions .. one row per student run (code + test result + AI review).

Cost rule: serve bank-first. Only generate a new problem when a cell is
exhausted, then persist it so it's a DB read forever after.
"""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:  # imported only for type checkers, not at runtime
    from app.models.user import User

# LONGTEXT on MySQL, plain TEXT on SQLite (tests) — same column, portable.
LongText = Text().with_variant(LONGTEXT(), "mysql")


def _uuid() -> str:
    return str(uuid.uuid4())


class ArenaProblem(Base):
    __tablename__ = "arena_problems"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    category: Mapped[str] = mapped_column(String(50), nullable=False)   # dsa|algorithms|math_ds|sql|ml
    topic: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    pattern_tag: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(12), nullable=False)  # Easy|Medium|Advanced

    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    statement: Mapped[Optional[str]] = mapped_column(LongText, nullable=True)

    examples_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)       # exactly 2 worked examples
    constraints_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    hints_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    starter_code_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    test_cases_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)     # visible + hidden

    optimal_solution: Mapped[Optional[str]] = mapped_column(LongText, nullable=True)
    complexity: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    source: Mapped[str] = mapped_column(String(10), default="seed", nullable=False)          # seed|auto
    review_status: Mapped[str] = mapped_column(String(12), default="published", nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    submissions: Mapped[list["ArenaSubmission"]] = relationship(
        back_populates="problem", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<ArenaProblem {self.category}/{self.difficulty} {self.title!r}>"


class ArenaSubmission(Base):
    __tablename__ = "arena_submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    problem_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("arena_problems.id"), index=True, nullable=False
    )

    language: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    code: Mapped[Optional[str]] = mapped_column(LongText, nullable=True)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    runtime_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_review_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship()
    problem: Mapped["ArenaProblem"] = relationship(back_populates="submissions")

    def __repr__(self) -> str:
        return f"<ArenaSubmission user={self.user_id} problem={self.problem_id} passed={self.passed}>"
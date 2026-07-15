# practice.py - [MOD] TopicQuestion (+ question_kind, review_status), UserAttempt
# backend/app/models/practice.py
"""
The core learning loop's data (Type-A curriculum + per-student attempts).

topic_content ...... one concept card per topic/subtopic (what/how/why + examples).
topic_questions .... 25 pre-written Q&A per subtopic (the practice bank).
user_attempts ...... one row per answered question (student answer + AI score).

CRITICAL cost rule: showing a question or revealing an answer is a pure DB read.
Only score_attempt() (practice_service.py) calls live AI. reveal_answer() reads
why/how/example/common_mistakes straight from topic_questions — never AI.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import User

def _uuid() -> str:
    return str(uuid.uuid4())


class TopicContent(Base):
    __tablename__ = "topic_content"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # One concept card per topic/subtopic.
    topic_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roadmap_topics.id", ondelete="CASCADE"),
        unique=True, index=True, nullable=False,
    )

    concept_markdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # the "what/how/why"
    examples_json: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)      # 4 worked examples

    # v12 Learn mode (learn_v12_service.py): {_what, _when, _how, _examples[5]}
    body_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    topic: Mapped["RoadmapTopic"] = relationship()  # noqa: F821

    def __repr__(self) -> str:
        return f"<TopicContent topic={self.topic_id}>"


class TopicQuestion(Base):
    __tablename__ = "topic_questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    topic_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("roadmap_topics.id", ondelete="CASCADE"), index=True, nullable=False
    )
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # v10 columns: 'text' | 'code' | 'math' | 'sql' (code opens the arena panel)
    question_kind: Mapped[str] = mapped_column(String(20), default="text", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(12), default="Easy", nullable=False)  # Easy|Medium|Advanced

    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    starter_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # for code questions
    model_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # sent to AI scorer, never shown raw

    # --- reveal content (pure DB read, no AI) ---
    why_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    how_explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    example: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    common_mistakes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # v10: 'draft' | 'published' | 'auto' | 'flagged'
    review_status: Mapped[str] = mapped_column(String(12), default="published", nullable=False)

    # v12 content pipeline (practice/analysis/content_qa _v12_service.py):
    # {question, examples[2], model_solution, why_how, common_mistakes[], starter_code}
    body_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # --- v12 25-question adaptive ordering ---
    position_index: Mapped[int] = mapped_column(Integer, default=1, nullable=False)      # 1..25 within a subtopic
    difficulty_tier: Mapped[str] = mapped_column(String(10), default="basic", nullable=False)  # basic|medium|advanced
    created_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    topic: Mapped["RoadmapTopic"] = relationship()  # noqa: F821
    attempts: Mapped[list["UserAttempt"]] = relationship(
        back_populates="question", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<TopicQuestion {self.difficulty}/{self.question_kind} topic={self.topic_id}>"


class UserAttempt(Base):
    __tablename__ = "user_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    question_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("topic_questions.id", ondelete="CASCADE"), index=True, nullable=False
    )

    student_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)          # 0-10 from AI
    ai_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    # Only the FIRST attempt counts toward mastery (System Understanding §5).
    is_first_attempt: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship()  # noqa: F821
    question: Mapped["TopicQuestion"] = relationship(back_populates="attempts")

    def __repr__(self) -> str:
        return f"<UserAttempt user={self.user_id} q={self.question_id} score={self.score}>"
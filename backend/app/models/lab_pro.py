# backend/app/models/lab_pro.py
"""
ATLAS AI 4.0 - v12 Live Lab Pro: models (spec Section 3).

Storage discipline (locked, carried from v11):
  the backend stores ONLY TEXT and METADATA - notebook cells, workspace
  .py/.sql/.md source, copilot cache. It NEVER stores uploaded datasets,
  images or trained models; those live and die in the student's browser
  (Pyodide virtual FS). Zero storage cost, privacy by schema.
"""

import uuid
from datetime import datetime, date

from sqlalchemy import (Column, String, Integer, Boolean, Text, JSON,
                        Date, DateTime, ForeignKey, UniqueConstraint, Index)

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class NotebookSession(Base):
    """One Live Lab Pro session: Colab-style cells + VS Code-style files
    share this row and ONE Pyodide kernel. Autosave is text-only."""

    __tablename__ = "labpro_sessions"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    title = Column(String(200), nullable=False, default="Untitled notebook")
    mode = Column(String(12), nullable=False, default="notebook")  # notebook|workspace
    active_env = Column(String(12), nullable=False, default="python")  # python|sql
    # [{"_id","_type":"code|markdown","_source","_output"}] underscore keys
    cells_json = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="active")  # active|archived
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (Index("ix_labpro_user_status", "user_id", "status"),)


class WorkspaceFile(Base):
    """VS Code-mode project tree. Text sources only; folders are rows
    with is_folder=1 and empty content."""

    __tablename__ = "labpro_workspace_files"

    id = Column(String(36), primary_key=True, default=_uuid)
    session_id = Column(String(36),
                        ForeignKey("labpro_sessions.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    path = Column(String(300), nullable=False)      # e.g. 'src/utils.py'
    is_folder = Column(Boolean, nullable=False, default=False)
    content = Column(Text, nullable=True)           # text only, capped in service
    size_chars = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("session_id", "path", name="uq_ws_session_path"),
    )


class LabProCopilotCache(Base):
    """Generate-once-cache for copilot answers, keyed by a content
    signature. Same code + same error -> same explanation, served free."""

    __tablename__ = "labpro_copilot_cache"

    id = Column(String(36), primary_key=True, default=_uuid)
    cache_key = Column(String(64), nullable=False, unique=True)  # sha256 hex
    action = Column(String(12), nullable=False)   # explain|suggest|fix|review
    response_json = Column(JSON, nullable=False)
    hit_count = Column(Integer, nullable=False, default=0)


class LabProCopilotUsage(Base):
    """Per-user daily cap on cache-MISS copilot calls (bounded Type B)."""

    __tablename__ = "labpro_copilot_usage"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), nullable=False, index=True)
    day = Column(Date, nullable=False, default=date.today)
    used = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("user_id", "day", name="uq_copilot_user_day"),
    )
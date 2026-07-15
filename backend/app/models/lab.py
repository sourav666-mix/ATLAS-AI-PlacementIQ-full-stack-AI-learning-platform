# FILE: app/models/lab.py
# BATCH 20 / v11 Phase 13 (new) - Live Lab tables, matching the v11 Guide §9
# DDL exactly: labs (catalog, Type A), lab_sessions (per-student TEXT +
# METADATA only), lab_datasets (curated starter library).
# HARD RULE: never store uploaded datasets or trained model files — only the
# student's code text, which tasks passed, and artifact names/sizes.

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, ForeignKey, Integer,
                        String, Text)

from app.database import Base


def _uid() -> str:
    return str(uuid.uuid4())


class Lab(Base):
    __tablename__ = "labs"

    id = Column(String(36), primary_key=True, default=_uid)
    domain_id = Column(String(36), ForeignKey("domains.id"), nullable=False)
    title = Column(String(200), nullable=False)
    # ds | analysis | ml | genai | mlops | cloud | cyber
    lab_type = Column(String(30), nullable=False, default="ds")
    starter_code = Column(Text)            # LONGTEXT in MySQL migration
    dataset_ref = Column(String(300))      # name/id in lab_datasets, or URL
    graded_tasks_json = Column(JSON)       # steps + hidden test cases
    needs_gpu = Column(Boolean, default=False)  # 1 = offers Colab bridge
    review_status = Column(String(12), default="published")


class LabSession(Base):
    __tablename__ = "lab_sessions"

    id = Column(String(36), primary_key=True, default=_uid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False)
    lab_id = Column(String(36), ForeignKey("labs.id"), nullable=False)
    code_snapshot = Column(Text)           # latest notebook TEXT only
    # v12 Live Lab 2.0 (text-only, zero storage cost)
    file_tree_json = Column(JSON, nullable=True)       # virtual-FS tree snapshot
    notebook_cells_json = Column(JSON, nullable=True)  # ordered cells + last output per cell
    tasks_passed_json = Column(JSON)       # which graded steps passed
    artifact_meta_json = Column(JSON)      # model/chart NAMES + SIZES only
    ai_review_json = Column(JSON, nullable=True)
    launched_colab = Column(Boolean, default=False)
    status = Column(String(20), default="in_progress")
    points_awarded = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class LabDataset(Base):
    __tablename__ = "lab_datasets"

    id = Column(String(36), primary_key=True, default=_uid)
    name = Column(String(150), nullable=False)
    domain_tag = Column(String(40))
    file_url = Column(String(400))
    rows_est = Column(Integer)
    size_kb = Column(Integer)
    description = Column(Text)
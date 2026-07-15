"""
ATLAS AI v12 — Career Target & Gap Engine models.
Tables: career_profiles, career_targets, company_benchmarks, career_gap_reports
All PKs are CHAR(36) UUID strings, matching the v10/v11/v12 convention.
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Integer, Float, Text, JSON, DateTime,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class CareerProfile(Base):
    """One row per student. The single source of truth for gap analysis inputs."""
    __tablename__ = "career_profiles"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, unique=True)

    # --- Identity / academics ---
    full_name = Column(String(150))
    degree = Column(String(40), default="B.Tech")
    branch = Column(String(80))                 # CSE / IT / ECE / EEE ...
    specialization = Column(String(120))        # e.g. "AI & ML", "Core CSE"
    college = Column(String(200))
    graduation_year = Column(Integer)
    cgpa = Column(Float)

    # --- Target ---
    target_domain = Column(String(60))          # data_science | backend | ...

    # --- Coding evidence ---
    leetcode_username = Column(String(80))
    leetcode_easy = Column(Integer, default=0)
    leetcode_medium = Column(Integer, default=0)
    leetcode_hard = Column(Integer, default=0)
    github_url = Column(String(300))
    linkedin_url = Column(String(300))

    # --- SQL / MySQL depth (self-declared, evidence-damped later) ---
    sql_level = Column(String(20), default="none")   # none|basic|intermediate|advanced
    sql_details = Column(Text)                       # "joins, group by, window fns"

    # --- Rich free-form structures ---
    skills_json = Column(JSON)          # [{name, category, label, details, evidence}]
    projects_json = Column(JSON)        # [{title, description, tech[], github, deployed, deployed_url, metrics}]
    internships_json = Column(JSON)     # [{company, role, months, work}]
    certifications_json = Column(JSON)  # [{name, issuer, year}]

    # --- Resume ---
    resume_filename = Column(String(300))
    resume_text = Column(Text)

    # --- Self reports (used only when no platform evidence exists) ---
    aptitude_self = Column(String(20), default="learning")
    communication_self = Column(String(20), default="learning")

    # --- Deterministic outputs (recomputed on every save, never AI-set) ---
    profile_score = Column(Integer, default=0)   # 0-100
    pillars_json = Column(JSON)                  # {pillar: 0-100}
    fingerprint = Column(String(64), index=True) # sha256 of canonical inputs

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    targets = relationship(
        "CareerTarget", back_populates="profile",
        cascade="all, delete-orphan", lazy="selectin",
    )


class CareerTarget(Base):
    """Up to 3 target companies per profile. Gap numbers are pure math."""
    __tablename__ = "career_targets"
    __table_args__ = (
        UniqueConstraint("profile_id", "company_slug", name="uq_profile_company"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    profile_id = Column(String(36), ForeignKey("career_profiles.id", ondelete="CASCADE"),
                        nullable=False)

    company_slug = Column(String(80), nullable=False)
    company_name = Column(String(150))
    priority = Column(Integer, default=1)        # 1 = dream, 2, 3 = safe

    readiness_pct = Column(Integer, default=0)   # 0-100
    gap_pct = Column(Integer, default=100)       # 100 - readiness
    pillar_gaps_json = Column(JSON)              # [{pillar, have, need, gap, weight, deficit_points}]
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    profile = relationship("CareerProfile", back_populates="targets")


class CompanyBenchmark(Base):
    """TYPE A. Seeded once by scripts/seed_company_benchmarks.py. Zero AI at read time."""
    __tablename__ = "company_benchmarks"
    __table_args__ = (
        UniqueConstraint("company_slug", "domain_slug", name="uq_company_domain"),
        Index("ix_bench_domain", "domain_slug"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    company_slug = Column(String(80), nullable=False)
    company_name = Column(String(150), nullable=False)
    archetype = Column(String(30))               # product | service | consulting | product_mid
    domain_slug = Column(String(60), nullable=False)

    hiring_bar = Column(Integer, default=70)     # 0-100, display only
    requirements_json = Column(JSON, nullable=False)  # {pillar: required 0-100}
    weights_json = Column(JSON, nullable=False)       # {pillar: weight, sums ~1.0}
    process_json = Column(JSON)                       # ["OA", "DSA round", "HR"]
    focus_notes = Column(Text)

    benchmark_version = Column(String(12), default="v12.1")
    created_at = Column(DateTime, default=datetime.utcnow)


class CareerGapReport(Base):
    """TYPE B cache. One AI call per unique fingerprint — forever."""
    __tablename__ = "career_gap_reports"
    __table_args__ = (
        UniqueConstraint("user_id", "fingerprint", name="uq_user_fingerprint"),
    )

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    profile_id = Column(String(36), ForeignKey("career_profiles.id", ondelete="CASCADE"),
                        nullable=False)

    fingerprint = Column(String(64), nullable=False, index=True)
    report_json = Column(JSON, nullable=False)
    source = Column(String(12), default="ai")    # ai | fallback
    model_used = Column(String(60))
    created_at = Column(DateTime, default=datetime.utcnow)
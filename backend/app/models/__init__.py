# backend/app/models/__init__.py
"""
Model registry — the complete v10 schema.

Importing app.models imports every ORM class so that:
  * SQLAlchemy can resolve cross-file relationships, and
  * Alembic autogenerate sees every table (via Base.metadata).

Batch 1:  user, plan, domain
Batch 2:  session, practice, skill_progress, daily_activity,
          leaderboard, tutor_history, college, admin_user, audit_log
Batch 3:  arena, job, championship, resume_doc, interview_studio, company_intel
"""
from app.database import Base  # noqa: F401  (re-exported for convenience)
from app.models.skillpath_v12 import DomainRoadmapItem   # noqa: F401
# --- Batch 1 ---
from app.models.user import User, PlacementProfile
from app.models.plan import SubscriptionPlan, UserSubscription
from app.models.domain import Domain, DomainPhase, RoadmapTopic

# --- Batch 2 ---
from app.models.session import MockSession, AptitudeSession
from app.models.practice import TopicContent, TopicQuestion, UserAttempt
from app.models.skill_progress import UserTopicProgress, SkillRadarScore
from app.models.daily_activity import DailyActivity
from app.models.leaderboard import Leaderboard, Badge, UserBadge
from app.models.tutor_history import TutorHistory
from app.models.college import College
from app.models.admin_user import AdminUser
from app.models.audit_log import AuditLog

# --- Batch 3 ---
from app.models.arena import ArenaProblem, ArenaSubmission
from app.models.job import JobPosting, JobTracking
from app.models.championship import Championship, ChampionshipAttempt
from app.models.resume_doc import ResumeDocument
from app.models.interview_studio import InterviewStudioSession
from app.models.company_intel import CompanyIntelCache

__all__ = [
    "Base",
    # Batch 1
    "User", "PlacementProfile",
    "SubscriptionPlan", "UserSubscription",
    "Domain", "DomainPhase", "RoadmapTopic",
    # Batch 2
    "MockSession", "AptitudeSession",
    "TopicContent", "TopicQuestion", "UserAttempt",
    "UserTopicProgress", "SkillRadarScore",
    "DailyActivity",
    "Leaderboard", "Badge", "UserBadge",
    "TutorHistory",
    "College", "AdminUser", "AuditLog",
    # Batch 3
    "ArenaProblem", "ArenaSubmission",
    "JobPosting", "JobTracking",
    "Championship", "ChampionshipAttempt",
    "ResumeDocument",
    "InterviewStudioSession",
    "CompanyIntelCache",
]

# --- v12 Live Lab Pro ---
from app.models.lab_pro import (        # noqa: F401
    NotebookSession, WorkspaceFile,
    LabProCopilotCache, LabProCopilotUsage,
)

# --- v12 Career Target & Gap Engine ---
from app.models.career_target import (      # noqa: F401
    CareerProfile, CareerTarget, CompanyBenchmark, CareerGapReport,
)
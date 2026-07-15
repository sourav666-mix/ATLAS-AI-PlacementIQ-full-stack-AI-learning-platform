# backend/alembic/versions/v12_001_skillpath_reforged.py
"""v12 SkillPath Reforged - schema delta (locked, spec Section 5).

Revision ID: v12_001
Revises: <set to your current head - run `alembic heads` and paste it>
Create Date: 2026-07-12

Delta:
  1. NEW  domain_roadmap_items  - domain roadmaps reference the shared
     topic library with per-domain order + phase + est_hours.
  2. ALTER user_topic_progress  + domain_id  (per-student-PER-DOMAIN
     progress; content shared, progress never).
  3. ALTER user_topic_progress  + progress_json (JSON) - underscore-keyed
     per-domain practice state: {_seen_qids,_answered,_correct,_score_sum}.
  4. ALTER roadmap_topics: domain_id becomes NULLable (shared-library
     topics carry no domain) + item_order for stable subtopic ordering
     (skipped automatically if the column already exists).
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = "v12_001"
down_revision = "v12_skillpath_engine"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in [c["name"] for c in inspect(bind).get_columns(table)]


def upgrade() -> None:
    # 1. the shared-library join table
    op.create_table(
        "domain_roadmap_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "domain_id", sa.String(36),
            sa.ForeignKey("domains.id", ondelete="CASCADE"), nullable=False,
        ),
        sa.Column(
            "topic_id", sa.String(36),
            sa.ForeignKey("roadmap_topics.id"), nullable=False,
        ),
        sa.Column("item_order", sa.Integer(), nullable=False),
        sa.Column("phase", sa.String(20), nullable=False,
                  server_default="Core"),
        sa.Column("est_hours", sa.Integer(), nullable=False,
                  server_default="6"),
        sa.UniqueConstraint("domain_id", "topic_id", name="uq_domain_topic"),
        sa.UniqueConstraint("domain_id", "item_order", name="uq_domain_order"),
    )
    op.create_index(
        "ix_dri_domain_order", "domain_roadmap_items",
        ["domain_id", "item_order"],
    )

    # 2 + 3. per-domain progress on user_topic_progress
    if not _has_column("user_topic_progress", "domain_id"):
        op.add_column(
            "user_topic_progress",
            sa.Column("domain_id", sa.String(36), nullable=True),
        )
        op.create_index(
            "ix_utp_user_domain", "user_topic_progress",
            ["user_id", "domain_id"],
        )
    if not _has_column("user_topic_progress", "progress_json"):
        op.add_column(
            "user_topic_progress",
            sa.Column("progress_json", sa.JSON(), nullable=True),
        )

    # 4. shared-library adjustments on roadmap_topics
    if _has_column("roadmap_topics", "domain_id"):
        op.alter_column(
            "roadmap_topics", "domain_id",
            existing_type=sa.String(36), nullable=True,
        )
    if not _has_column("roadmap_topics", "item_order"):
        op.add_column(
            "roadmap_topics",
            sa.Column("item_order", sa.Integer(), nullable=True),
        )
    # stable ordering column for auto-appended questions
    if not _has_column("topic_questions", "created_order"):
        op.add_column(
            "topic_questions",
            sa.Column("created_order", sa.Integer(), nullable=True),
        )


def downgrade() -> None:
    op.drop_index("ix_dri_domain_order", table_name="domain_roadmap_items")
    op.drop_table("domain_roadmap_items")
    if _has_column("user_topic_progress", "progress_json"):
        op.drop_column("user_topic_progress", "progress_json")
    if _has_column("user_topic_progress", "domain_id"):
        op.drop_index("ix_utp_user_domain", table_name="user_topic_progress")
        op.drop_column("user_topic_progress", "domain_id")
    if _has_column("topic_questions", "created_order"):
        op.drop_column("topic_questions", "created_order")
    if _has_column("roadmap_topics", "item_order"):
        op.drop_column("roadmap_topics", "item_order")

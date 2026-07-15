# backend/alembic/versions/v12_004_roadmap_topics_phase_nullable.py
"""v12 SkillPath Reforged fix - roadmap_topics.phase_id becomes NULLable.

Revision ID: v12_004
Revises: v12_003
Create Date: 2026-07-15

v12_001 made roadmap_topics.domain_id NULLable for shared-library topics
(one topic row reused across domains via domain_roadmap_items) but missed
phase_id, which is still NOT NULL — shared-library topics carry no single
phase (phase is now per-domain, on DomainRoadmapItem.phase), so inserting
one always violated the NOT NULL constraint. This just finishes that delta.
"""

from alembic import op
import sqlalchemy as sa

revision = "v12_004"
down_revision = "v12_003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "roadmap_topics", "phase_id",
        existing_type=sa.String(36), nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "roadmap_topics", "phase_id",
        existing_type=sa.String(36), nullable=False,
    )

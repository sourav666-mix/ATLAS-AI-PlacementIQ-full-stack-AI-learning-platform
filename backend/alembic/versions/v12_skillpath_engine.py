# backend/alembic/versions/v12_skillpath_engine.py   [NEW v12]
"""v12 SkillPath Engine 3.0 — new tables + additive alters

Revision ID: v12_skillpath_engine
Revises: <SET_TO_YOUR_CURRENT_HEAD>     # NOTE: run `alembic heads` and paste it here
Create Date: 2026-07-12
"""
import sqlalchemy as sa
from alembic import op

revision = "v12_skillpath_engine"
down_revision = "v11_0001_labs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- shared content library (de-dup layer) ---
    op.create_table(
        "content_library",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("module_key", sa.String(60), nullable=False, unique=True),
        sa.Column("title", sa.String(150), nullable=False),
        sa.Column("subtopics_json", sa.JSON(), nullable=True),
    )
    op.create_table(
        "domain_topic_map",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("domain_id", sa.String(36), sa.ForeignKey("domains.id"), nullable=False),
        sa.Column("content_module_id", sa.String(36), sa.ForeignKey("content_library.id"), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="1"),
        sa.UniqueConstraint("domain_id", "content_module_id", name="uq_domain_module"),
    )

    # --- per-student progress + multi-domain enrollment ---
    op.create_table(
        "subtopic_progress",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subtopic_id", sa.String(36), nullable=False),
        sa.Column("questions_completed", sa.Integer(), server_default="0"),
        sa.Column("mastery_score", sa.Integer(), server_default="0"),
        sa.Column("status", sa.String(12), server_default="locked"),
        sa.UniqueConstraint("user_id", "subtopic_id", name="uq_user_subtopic"),
    )
    op.create_table(
        "domain_enrollments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("domain_id", sa.String(36), sa.ForeignKey("domains.id"), nullable=False),
        sa.Column("plan_id", sa.String(36), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "domain_id", name="uq_user_domain"),
    )

    # --- additive alters (Section 8) ---
    op.add_column("roadmap_topics", sa.Column("what_is_it", sa.Text(), nullable=True))
    op.add_column("roadmap_topics", sa.Column("when_to_use", sa.Text(), nullable=True))
    op.add_column("roadmap_topics", sa.Column("how_to_use", sa.Text(), nullable=True))
    op.add_column("roadmap_topics", sa.Column("examples_json", sa.JSON(), nullable=True))
    op.add_column("roadmap_topics", sa.Column("visualization_config_json", sa.JSON(), nullable=True))

    op.add_column("topic_questions", sa.Column("position_index", sa.Integer(), server_default="1"))
    op.add_column("topic_questions", sa.Column("difficulty_tier", sa.String(10), server_default="basic"))

    op.add_column("lab_sessions", sa.Column("file_tree_json", sa.JSON(), nullable=True))
    op.add_column("lab_sessions", sa.Column("notebook_cells_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("lab_sessions", "notebook_cells_json")
    op.drop_column("lab_sessions", "file_tree_json")
    op.drop_column("topic_questions", "difficulty_tier")
    op.drop_column("topic_questions", "position_index")
    for col in ("visualization_config_json", "examples_json", "how_to_use", "when_to_use", "what_is_it"):
        op.drop_column("roadmap_topics", col)
    op.drop_table("domain_enrollments")
    op.drop_table("subtopic_progress")
    op.drop_table("domain_topic_map")
    op.drop_table("content_library")
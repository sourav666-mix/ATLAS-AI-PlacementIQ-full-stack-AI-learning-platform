# FILE: alembic/versions/v11_0001_labs_tables.py
# BATCH 20 / v11 Phase 13 (new) - Migration: the three v11 tables.
#
# ONE MANUAL STEP BEFORE RUNNING (do it now):
#   run `alembic heads` in backend/ and put that revision id into
#   down_revision below, replacing REPLACE_WITH_CURRENT_HEAD.
# Then: alembic upgrade head  ->  SHOW TABLES; must list labs, lab_sessions,
# lab_datasets (34 tables total).

from alembic import op
import sqlalchemy as sa

revision = "v11_0001_labs"
down_revision = "2bcc5fe944f3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "labs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("domain_id", sa.String(36),
                  sa.ForeignKey("domains.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("lab_type", sa.String(30), nullable=False,
                  server_default="ds"),
        sa.Column("starter_code", sa.Text().with_variant(
            sa.dialects.mysql.LONGTEXT(), "mysql")),
        sa.Column("dataset_ref", sa.String(300)),
        sa.Column("graded_tasks_json", sa.JSON()),
        sa.Column("needs_gpu", sa.Boolean(), server_default=sa.text("0")),
        sa.Column("review_status", sa.String(12),
                  server_default="published"),
    )
    op.create_table(
        "lab_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("lab_id", sa.String(36), sa.ForeignKey("labs.id"),
                  nullable=False),
        sa.Column("code_snapshot", sa.Text().with_variant(
            sa.dialects.mysql.LONGTEXT(), "mysql")),
        sa.Column("tasks_passed_json", sa.JSON()),
        sa.Column("artifact_meta_json", sa.JSON()),
        sa.Column("ai_review_json", sa.JSON(), nullable=True),
        sa.Column("launched_colab", sa.Boolean(),
                  server_default=sa.text("0")),
        sa.Column("status", sa.String(20), server_default="in_progress"),
        sa.Column("points_awarded", sa.Integer(), server_default="0"),
        sa.Column("updated_at", sa.TIMESTAMP(),
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_lab_sessions_user_lab", "lab_sessions",
                    ["user_id", "lab_id"], unique=True)
    op.create_table(
        "lab_datasets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(150), nullable=False),
        sa.Column("domain_tag", sa.String(40)),
        sa.Column("file_url", sa.String(400)),
        sa.Column("rows_est", sa.Integer()),
        sa.Column("size_kb", sa.Integer()),
        sa.Column("description", sa.Text()),
    )


def downgrade() -> None:
    op.drop_index("ix_lab_sessions_user_lab", table_name="lab_sessions")
    op.drop_table("lab_sessions")
    op.drop_table("lab_datasets")
    op.drop_table("labs")
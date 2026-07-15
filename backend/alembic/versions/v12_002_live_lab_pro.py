# backend/alembic/versions/v12_002_live_lab_pro.py
"""v12 Live Lab Pro - schema delta.

Revision ID: v12_002
Revises: v12_001
Create Date: 2026-07-12

Delta (all NEW tables; nothing existing is touched):
  labpro_sessions         one row per notebook session (text-only autosave)
  labpro_workspace_files  VS Code-mode project tree (text sources only)
  labpro_copilot_cache    generate-once-cache for copilot answers
  labpro_copilot_usage    per-user daily cap on cache-miss copilot calls
"""

from alembic import op
import sqlalchemy as sa

revision = "v12_002"
down_revision = "v12_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "labpro_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("title", sa.String(200), nullable=False,
                  server_default="Untitled notebook"),
        sa.Column("mode", sa.String(12), nullable=False,
                  server_default="notebook"),
        sa.Column("active_env", sa.String(12), nullable=False,
                  server_default="python"),
        sa.Column("cells_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False,
                  server_default="active"),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_labpro_user_status", "labpro_sessions",
                    ["user_id", "status"])

    op.create_table(
        "labpro_workspace_files",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("session_id", sa.String(36),
                  sa.ForeignKey("labpro_sessions.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("path", sa.String(300), nullable=False),
        sa.Column("is_folder", sa.Boolean(), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("size_chars", sa.Integer(), nullable=False,
                  server_default="0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("session_id", "path", name="uq_ws_session_path"),
    )
    op.create_index("ix_ws_session", "labpro_workspace_files", ["session_id"])

    op.create_table(
        "labpro_copilot_cache",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("cache_key", sa.String(64), nullable=False, unique=True),
        sa.Column("action", sa.String(12), nullable=False),
        sa.Column("response_json", sa.JSON(), nullable=False),
        sa.Column("hit_count", sa.Integer(), nullable=False,
                  server_default="0"),
    )

    op.create_table(
        "labpro_copilot_usage",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("used", sa.Integer(), nullable=False, server_default="0"),
        sa.UniqueConstraint("user_id", "day", name="uq_copilot_user_day"),
    )
    op.create_index("ix_copilot_usage_user", "labpro_copilot_usage",
                    ["user_id"])


def downgrade() -> None:
    op.drop_table("labpro_copilot_usage")
    op.drop_table("labpro_copilot_cache")
    op.drop_table("labpro_workspace_files")
    op.drop_index("ix_labpro_user_status", table_name="labpro_sessions")
    op.drop_table("labpro_sessions")
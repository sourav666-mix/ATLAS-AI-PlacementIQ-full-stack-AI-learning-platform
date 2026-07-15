# backend/alembic/versions/v12_003_career_target.py
"""v12 Career Target & Gap Engine - schema delta.

Revision ID: v12_003
Revises: v12_002
Create Date: 2026-07-15

Delta (all NEW tables; nothing existing is touched):
  career_profiles       one row per student, source of truth for gap inputs
  career_targets        up to 3 target companies per profile
  company_benchmarks    seeded hiring bars / requirements per company+domain
  career_gap_reports    cache of the one AI call per unique fingerprint
"""

from alembic import op
import sqlalchemy as sa

revision = "v12_003"
down_revision = "v12_002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "career_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False, unique=True),
        sa.Column("full_name", sa.String(150), nullable=True),
        sa.Column("degree", sa.String(40), nullable=True, server_default="B.Tech"),
        sa.Column("branch", sa.String(80), nullable=True),
        sa.Column("specialization", sa.String(120), nullable=True),
        sa.Column("college", sa.String(200), nullable=True),
        sa.Column("graduation_year", sa.Integer(), nullable=True),
        sa.Column("cgpa", sa.Float(), nullable=True),
        sa.Column("target_domain", sa.String(60), nullable=True),
        sa.Column("leetcode_username", sa.String(80), nullable=True),
        sa.Column("leetcode_easy", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("leetcode_medium", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("leetcode_hard", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("github_url", sa.String(300), nullable=True),
        sa.Column("linkedin_url", sa.String(300), nullable=True),
        sa.Column("sql_level", sa.String(20), nullable=True, server_default="none"),
        sa.Column("sql_details", sa.Text(), nullable=True),
        sa.Column("skills_json", sa.JSON(), nullable=True),
        sa.Column("projects_json", sa.JSON(), nullable=True),
        sa.Column("internships_json", sa.JSON(), nullable=True),
        sa.Column("certifications_json", sa.JSON(), nullable=True),
        sa.Column("resume_filename", sa.String(300), nullable=True),
        sa.Column("resume_text", sa.Text(), nullable=True),
        sa.Column("aptitude_self", sa.String(20), nullable=True, server_default="learning"),
        sa.Column("communication_self", sa.String(20), nullable=True, server_default="learning"),
        sa.Column("profile_score", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("pillars_json", sa.JSON(), nullable=True),
        sa.Column("fingerprint", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_career_profiles_fingerprint", "career_profiles", ["fingerprint"])

    op.create_table(
        "career_targets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("profile_id", sa.String(36),
                  sa.ForeignKey("career_profiles.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("company_slug", sa.String(80), nullable=False),
        sa.Column("company_name", sa.String(150), nullable=True),
        sa.Column("priority", sa.Integer(), nullable=True, server_default="1"),
        sa.Column("readiness_pct", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("gap_pct", sa.Integer(), nullable=True, server_default="100"),
        sa.Column("pillar_gaps_json", sa.JSON(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("profile_id", "company_slug", name="uq_profile_company"),
    )

    op.create_table(
        "company_benchmarks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_slug", sa.String(80), nullable=False),
        sa.Column("company_name", sa.String(150), nullable=False),
        sa.Column("archetype", sa.String(30), nullable=True),
        sa.Column("domain_slug", sa.String(60), nullable=False),
        sa.Column("hiring_bar", sa.Integer(), nullable=True, server_default="70"),
        sa.Column("requirements_json", sa.JSON(), nullable=False),
        sa.Column("weights_json", sa.JSON(), nullable=False),
        sa.Column("process_json", sa.JSON(), nullable=True),
        sa.Column("focus_notes", sa.Text(), nullable=True),
        sa.Column("benchmark_version", sa.String(12), nullable=True, server_default="v12.1"),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("company_slug", "domain_slug", name="uq_company_domain"),
    )
    op.create_index("ix_bench_domain", "company_benchmarks", ["domain_slug"])

    op.create_table(
        "career_gap_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("profile_id", sa.String(36),
                  sa.ForeignKey("career_profiles.id", ondelete="CASCADE"),
                  nullable=False),
        sa.Column("fingerprint", sa.String(64), nullable=False),
        sa.Column("report_json", sa.JSON(), nullable=False),
        sa.Column("source", sa.String(12), nullable=True, server_default="ai"),
        sa.Column("model_used", sa.String(60), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False,
                  server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("user_id", "fingerprint", name="uq_user_fingerprint"),
    )
    op.create_index("ix_career_gap_reports_fingerprint", "career_gap_reports", ["fingerprint"])


def downgrade() -> None:
    op.drop_table("career_gap_reports")
    op.drop_index("ix_bench_domain", table_name="company_benchmarks")
    op.drop_table("company_benchmarks")
    op.drop_table("career_targets")
    op.drop_index("ix_career_profiles_fingerprint", table_name="career_profiles")
    op.drop_table("career_profiles")

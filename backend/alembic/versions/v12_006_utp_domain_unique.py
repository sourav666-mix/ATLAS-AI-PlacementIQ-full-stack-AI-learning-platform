# backend/alembic/versions/v12_006_utp_domain_unique.py
"""v12 SkillPath Reforged fix - user_topic_progress uniqueness widens to
include domain_id.

Revision ID: v12_006
Revises: v12_005
Create Date: 2026-07-15

v12_001 added user_topic_progress.domain_id for "per-student-PER-DOMAIN
progress" (a shared-library topic can be reused across multiple domains,
e.g. via domain_roadmap_items) but left the old uq_user_topic (user_id,
topic_id) unique constraint in place. practice_v12_service.get_or_create_utp
looks a row up by (user_id, topic_id, domain_id) and inserts on miss, which
IntegrityErrors the moment the same topic is progressed under a second
domain for the same user. Widen the constraint to match the documented
intent.
"""

from alembic import op
import sqlalchemy as sa

revision = "v12_006"
down_revision = "v12_005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("uq_user_topic", "user_topic_progress", type_="unique")
    op.create_unique_constraint(
        "uq_user_topic_domain", "user_topic_progress",
        ["user_id", "topic_id", "domain_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_user_topic_domain", "user_topic_progress", type_="unique")
    op.create_unique_constraint(
        "uq_user_topic", "user_topic_progress", ["user_id", "topic_id"],
    )

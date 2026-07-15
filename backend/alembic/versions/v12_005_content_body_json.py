# backend/alembic/versions/v12_005_content_body_json.py
"""v12 content pipeline - add body_json to topic_content + topic_questions.

Revision ID: v12_005
Revises: v12_004
Create Date: 2026-07-15

learn_v12_service.py, practice_v12_service.py, analysis_v12_service.py,
content_qa_service.py and both seed scripts (seed_content.py, seed_gate.py)
all read/write a JSON `body_json` blob on these two tables
(topic_content: {_what,_when,_how,_examples[5]};
 topic_questions: {question,examples[2],model_solution,why_how,
 common_mistakes,starter_code}) but the column was never added to either
table — every v12 Learn/Practice/Analysis call was failing.
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "v12_005"
down_revision = "v12_004"
branch_labels = None
depends_on = None


def _has_column(table: str, column: str) -> bool:
    bind = op.get_bind()
    return column in [c["name"] for c in inspect(bind).get_columns(table)]


def upgrade() -> None:
    if not _has_column("topic_content", "body_json"):
        op.add_column(
            "topic_content",
            sa.Column("body_json", sa.JSON(), nullable=True),
        )
    if not _has_column("topic_questions", "body_json"):
        op.add_column(
            "topic_questions",
            sa.Column("body_json", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    if _has_column("topic_questions", "body_json"):
        op.drop_column("topic_questions", "body_json")
    if _has_column("topic_content", "body_json"):
        op.drop_column("topic_content", "body_json")

"""Store the Docs documents holding recording summaries.

Adds the ``meeting.docs_document_id`` column pointing at the Docs document
gathering a meeting summaries, and the ``recording_document`` table associating
each BBB recording with its own sub-document.

Revision ID: b7c4e1d90f32
Revises: a3a6e932b2ae
Create Date: 2026-07-29 10:12:03.114287

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b7c4e1d90f32"
down_revision = "a3a6e932b2ae"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recording_document",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("recording_id", sa.Unicode(length=100), nullable=False),
        sa.Column("document_id", sa.Unicode(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["meeting_id"], ["meeting.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "recording_id"),
    )
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("docs_document_id", sa.Unicode(length=50), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("docs_document_id")

    op.drop_table("recording_document")

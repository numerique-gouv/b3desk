"""create meeting_session table.

Adds the ``meeting_session`` table to track each BBB session (start/end
time and, once available, the recording ID) for a persistent meeting, so
the meeting history page doesn't have to be reconstructed from
``getRecordings`` alone.

Revision ID: 8ad73a0e3e3b
Revises: a3a6e932b2ae
Create Date: 2026-08-04 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "8ad73a0e3e3b"
down_revision = "a3a6e932b2ae"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "meeting_session",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.Column("recording_id", sa.Unicode(length=250), nullable=True),
        sa.ForeignKeyConstraint(
            ["meeting_id"], ["meeting.id"], name="meeting_session_meeting_id_fkey"
        ),
        sa.PrimaryKeyConstraint("id", name="meeting_session_pkey"),
    )


def downgrade():
    op.drop_table("meeting_session")

"""removes meeting_files_external table.

Revision ID: 9869cacd37a4
Revises: f68adee062bf
Create Date: 2025-10-23 08:37:34.743064

"""

import sqlalchemy as sa
from alembic import op

revision = "9869cacd37a4"
down_revision = "f68adee062bf"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("meeting_files_external")


def downgrade():
    op.create_table(
        "meeting_files_external",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column(
            "title", sa.VARCHAR(length=4096), autoincrement=False, nullable=False
        ),
        sa.Column(
            "nc_path", sa.VARCHAR(length=4096), autoincrement=False, nullable=True
        ),
        sa.Column("meeting_id", sa.INTEGER(), autoincrement=False, nullable=False),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meeting.id"],
            name=op.f("meeting_files_external_meeting_id_fkey"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("meeting_files_external_pkey")),
    )

"""create_meeting_files_table

Revision ID: 1094e771bd3f
Revises: 8fe077ecfb10
Create Date: 2023-02-28 14:30:43.642893

"""
import os
import sys

import sqlalchemy as sa
from alembic import op

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import alembic_helpers


# revision identifiers, used by Alembic.
revision = "1094e771bd3f"
down_revision = "8fe077ecfb10"
branch_labels = None
depends_on = None


def upgrade():
    if alembic_helpers.table_does_not_exist("meeting_files"):
        op.create_table(
            "meeting_files",
            sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
            sa.Column(
                "title", sa.VARCHAR(length=4096), autoincrement=False, nullable=False
            ),
            sa.Column(
                "url", sa.VARCHAR(length=4096), autoincrement=False, nullable=True
            ),
            sa.Column(
                "nc_path", sa.VARCHAR(length=4096), autoincrement=False, nullable=True
            ),
            sa.Column("meeting_id", sa.INTEGER(), autoincrement=False, nullable=False),
            sa.Column("is_default", sa.BOOLEAN(), autoincrement=False, nullable=True),
            sa.Column(
                "is_downloadable", sa.BOOLEAN(), autoincrement=False, nullable=True
            ),
            sa.Column("created_at", sa.DATE(), autoincrement=False, nullable=True),
            sa.ForeignKeyConstraint(
                ["meeting_id"], ["meeting.id"], name="meeting_files_meeting_id_fkey"
            ),
            sa.PrimaryKeyConstraint("id", name="meeting_files_pkey"),
        )

    if alembic_helpers.table_does_not_exist("meeting_files_external"):
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
                name="meeting_files_external_meeting_id_fkey",
            ),
            sa.PrimaryKeyConstraint("id", name="meeting_files_external_pkey"),
        )


def downgrade():
    if not alembic_helpers.table_does_not_exist("meeting_files"):
        op.drop_table("meeting_files")
    if not alembic_helpers.table_does_not_exist("meeting_files_external"):
        op.drop_table("meeting_files_external")

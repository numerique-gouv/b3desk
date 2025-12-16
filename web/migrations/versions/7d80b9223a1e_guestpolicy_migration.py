"""GuestPolicy migration.

Revision ID: 7d80b9223a1e
Revises: 54f71a7705a8
Create Date: 2023-02-28 14:29:28.456201
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "7d80b9223a1e"
down_revision = "54f71a7705a8"
branch_labels = None
depends_on = None


def table_has_column(table, column):
    columns = [col["name"] for col in inspect(op.get_bind()).get_columns(table)]
    return column in columns


def upgrade():
    if not table_has_column("meeting", "guestPolicy"):
        op.add_column("meeting", sa.Column("guestPolicy", sa.Boolean(), nullable=True))


def downgrade():
    if table_has_column("meeting", "guestPolicy"):
        op.drop_column("meeting", "guestPolicy")

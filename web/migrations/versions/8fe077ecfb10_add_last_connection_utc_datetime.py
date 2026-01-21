"""Add last_connection_utc_datetime.

Revision ID: 8fe077ecfb10
Revises: 9aac3b5e1582
Create Date: 2022-08-12 09:09:47.674373
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "8fe077ecfb10"
down_revision = "9aac3b5e1582"
branch_labels = None
depends_on = None


def table_has_column(table, column):
    columns = [col["name"] for col in inspect(op.get_bind()).get_columns(table)]
    return column in columns


def upgrade():
    if not table_has_column("user", "last_connection_utc_datetime"):
        op.add_column(
            "user",
            sa.Column("last_connection_utc_datetime", sa.DateTime(), nullable=True),
        )


def downgrade():
    if table_has_column("user", "last_connection_utc_datetime"):
        op.drop_column("user", "last_connection_utc_datetime")

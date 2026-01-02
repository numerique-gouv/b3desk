"""add_user_nextcloud_connection_info.

Revision ID: 65acbe9b0646
Revises: 1094e771bd3f
Create Date: 2023-02-28 14:35:21.691915
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "65acbe9b0646"
down_revision = "1094e771bd3f"
branch_labels = None
depends_on = None


def table_has_column(table, column):
    columns = [col["name"] for col in inspect(op.get_bind()).get_columns(table)]
    return column in columns


def upgrade():
    if not table_has_column("user", "nc_locator"):
        op.add_column(
            "user",
            sa.Column(
                "nc_locator", sa.VARCHAR(length=255), autoincrement=False, nullable=True
            ),
        )
    if not table_has_column("user", "nc_login"):
        op.add_column(
            "user",
            sa.Column(
                "nc_login", sa.VARCHAR(length=255), autoincrement=False, nullable=True
            ),
        )
    if not table_has_column("user", "nc_token"):
        op.add_column(
            "user",
            sa.Column(
                "nc_token", sa.VARCHAR(length=255), autoincrement=False, nullable=True
            ),
        )
    if not table_has_column("user", "nc_last_auto_enroll"):
        op.add_column(
            "user",
            sa.Column(
                "nc_last_auto_enroll", sa.DateTime(), autoincrement=False, nullable=True
            ),
        )


def downgrade():
    if table_has_column("user", "nc_locator"):
        op.drop_column("user", "nc_locator")
    if table_has_column("user", "nc_login"):
        op.drop_column("user", "nc_login")
    if table_has_column("user", "nc_token"):
        op.drop_column("user", "nc_token")
    if table_has_column("user", "nc_last_auto_enroll"):
        op.drop_column("user", "nc_last_auto_enroll")

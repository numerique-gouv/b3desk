"""Adds shadow meeting.

Revision ID: 2e95af7b75cf
Revises: c25342fd2428
Create Date: 2025-04-03 09:45:25.516987
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2e95af7b75cf"
down_revision = "c25342fd2428"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("last_connection_utc_datetime", sa.DateTime(), nullable=True)
        )
        batch_op.add_column(sa.Column("is_shadow", sa.Boolean(), nullable=True))


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("is_shadow")
        batch_op.drop_column("last_connection_utc_datetime")

"""Add created_at field in user.

Revision ID: 454adc444042
Revises: 3c8b6c640fee
Create Date: 2025-09-03 08:36:49.556214

"""

import sqlalchemy as sa
from alembic import op

revision = "454adc444042"
down_revision = "3c8b6c640fee"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "created_at",
                sa.DateTime(),
                nullable=False,
                server_default=sa.text("'1900-01-01 00:00:00'"),
            )
        )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("created_at", server_default=None)


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("created_at")

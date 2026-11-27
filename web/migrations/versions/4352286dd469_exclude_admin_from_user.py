"""exclude admin from user.

Revision ID: 4352286dd469
Revises: a3203f74e042
Create Date: 2026-11-12 12:29:30.944989
"""

import sqlalchemy as sa
from alembic import op

revision = "4352286dd469"
down_revision = "a3203f74e042"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("admin")


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("admin", sa.Boolean(), nullable=False, server_default=sa.false())
        )

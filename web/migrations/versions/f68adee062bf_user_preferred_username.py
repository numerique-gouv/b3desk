"""Add user.preferred_username.

Revision ID: f68adee062bf
Revises: 454adc444042
Create Date: 2025-09-24 14:02:41.018692

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f68adee062bf"
down_revision = "454adc444042"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("preferred_username", sa.Unicode(length=50), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("preferred_username")

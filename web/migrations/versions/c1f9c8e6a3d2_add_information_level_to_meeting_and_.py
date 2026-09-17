"""add information_level to meeting and user.

Tracks how far along the pre-deletion warning sequence (0 to 3) a meeting or
user account is, and when the last warning mail was sent, so the deletion
cron tasks never delete an entity that was not actually informed.

Revision ID: c1f9c8e6a3d2
Revises: a3203f74e042
Create Date: 2026-09-04 10:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c1f9c8e6a3d2"
down_revision = "a3203f74e042"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "information_level", sa.Integer(), nullable=False, server_default="0"
            )
        )
        batch_op.add_column(
            sa.Column("information_sent_at", sa.DateTime(), nullable=True)
        )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "information_level", sa.Integer(), nullable=False, server_default="0"
            )
        )
        batch_op.add_column(
            sa.Column("information_sent_at", sa.DateTime(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("information_sent_at")
        batch_op.drop_column("information_level")

    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("information_sent_at")
        batch_op.drop_column("information_level")

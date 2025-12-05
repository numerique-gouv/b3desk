"""Rename Meeting.user_id to owner_id.

Revision ID: a1b2c3d4e5f6
Revises: 77f91494af65
Create Date: 2025-12-02 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "77f91494af65"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column("user_id", new_column_name="owner_id")


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column("owner_id", new_column_name="user_id")

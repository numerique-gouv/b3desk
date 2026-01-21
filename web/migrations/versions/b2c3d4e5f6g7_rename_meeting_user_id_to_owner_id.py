"""Rename Meeting.user_id to owner_id.

Revision ID: b2c3d4e5f6g7
Revises: 77f91494af65
Create Date: 2025-12-02 10:00:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b2c3d4e5f6g7"
down_revision = "77f91494af65"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column("user_id", new_column_name="owner_id")

    # Update meeting_files.owner_id for files that weren't populated
    op.execute(
        """
        UPDATE meeting_files
        SET owner_id = (SELECT owner_id FROM meeting WHERE meeting.id = meeting_files.meeting_id)
        WHERE owner_id IS NULL
        """
    )


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column("owner_id", new_column_name="user_id")

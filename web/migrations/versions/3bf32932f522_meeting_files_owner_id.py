"""Add meeting_files.owner_id.

Revision ID: 3bf32932f522
Revises: 9a4ffc3a0f0d
Create Date: 2026-01-08

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3bf32932f522"
down_revision = "9a4ffc3a0f0d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting_files", schema=None) as batch_op:
        batch_op.add_column(sa.Column("owner_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_meeting_files_owner_id", "user", ["owner_id"], ["id"]
        )

    # Populate owner_id from meeting.user_id for existing files
    op.execute(
        """
        UPDATE meeting_files
        SET owner_id = (SELECT user_id FROM meeting WHERE meeting.id = meeting_files.meeting_id)
        """
    )


def downgrade():
    with op.batch_alter_table("meeting_files", schema=None) as batch_op:
        batch_op.drop_constraint("fk_meeting_files_owner_id", type_="foreignkey")
        batch_op.drop_column("owner_id")

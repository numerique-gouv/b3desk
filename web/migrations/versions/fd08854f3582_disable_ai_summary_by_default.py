"""disable ai summary by default.

Revision ID: fd08854f3582
Revises: 791755877bb1
Create Date: 2026-06-19 11:21:43.005310

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "fd08854f3582"
down_revision = "791755877bb1"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "meta_disable_recording_ai_summary",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("meta_disable_recording_ai_summary")

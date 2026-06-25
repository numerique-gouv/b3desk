"""shadow_meeting replaced by hidden_meeting.

Revision ID: df718f7e4106
Revises: a3a6e932b2ae
Create Date: 2026-06-25 13:50:23.238229

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "df718f7e4106"
down_revision = "a3a6e932b2ae"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column("is_shadow", new_column_name="is_hidden")


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column("is_hidden", new_column_name="is_shadow")

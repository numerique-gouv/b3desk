"""Remove is_default from meeting_files.

Revision ID: a1b2c3d4e5f6
Revises: 3bf32932f522
Create Date: 2026-01-14

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "3bf32932f522"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting_files", schema=None) as batch_op:
        batch_op.drop_column("is_default")


def downgrade():
    with op.batch_alter_table("meeting_files", schema=None) as batch_op:
        batch_op.add_column(sa.Column("is_default", sa.Boolean(), nullable=True))

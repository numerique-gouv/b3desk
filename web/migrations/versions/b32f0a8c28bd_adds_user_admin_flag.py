"""adds user admin flag.

Revision ID: b32f0a8c28bd
Revises: 9dd2b54b4b11
Create Date: 2026-05-13 12:30:16.161599

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b32f0a8c28bd"
down_revision = "9dd2b54b4b11"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "admin",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            )
        )
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("admin", server_default=None)


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("admin")

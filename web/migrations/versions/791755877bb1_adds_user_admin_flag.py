"""adds user admin flag.

Revision ID: 791755877bb1
Revises: 9dd2b54b4b11
Create Date: 2026-06-04 10:05:59.068085

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "791755877bb1"
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
                server_default=sa.false(),
            )
        )

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("admin", server_default=None)


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("admin")

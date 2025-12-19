"""increase email and preferred_username length.

Revision ID: 9a4ffc3a0f0d
Revises: 9869cacd37a4
Create Date: 2025-12-16 11:12:54.373618

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9a4ffc3a0f0d"
down_revision = "9869cacd37a4"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column(
            "email",
            existing_type=sa.VARCHAR(length=150),
            type_=sa.Unicode(length=255),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "preferred_username",
            existing_type=sa.VARCHAR(length=50),
            type_=sa.Unicode(length=255),
            existing_nullable=True,
        )


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column(
            "preferred_username",
            existing_type=sa.Unicode(length=255),
            type_=sa.VARCHAR(length=50),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "email",
            existing_type=sa.Unicode(length=255),
            type_=sa.VARCHAR(length=150),
            existing_nullable=True,
        )

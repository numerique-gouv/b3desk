"""visio_code length.

Revision ID: 3c8b6c640fee
Revises: 0052f608f4b3
Create Date: 2025-08-05 09:40:39.334078
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "3c8b6c640fee"
down_revision = "0052f608f4b3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column(
            "visio_code",
            existing_type=sa.String(),
            type_=sa.VARCHAR(length=50),
            existing_nullable=False,
            nullable=False,
        )


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column(
            "visio_code",
            existing_type=sa.VARCHAR(length=50),
            type_=sa.String(),
            existing_nullable=False,
            nullable=False,
        )

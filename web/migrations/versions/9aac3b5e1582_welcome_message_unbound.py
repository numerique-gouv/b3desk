"""Welcome message unbound.

Revision ID: 9aac3b5e1582
Revises: 7d80b9223a1e
Create Date: 2021-05-06 17:44:17.835474
"""
import os
import sys

import sqlalchemy as sa
from alembic import op

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)


# revision identifiers, used by Alembic.
revision = "9aac3b5e1582"
down_revision = "7d80b9223a1e"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        "meeting", "welcome", existing_type=sa.Unicode(150), type=sa.UnicodeText()
    )


def downgrade():
    op.alter_column(
        "meeting", "welcome", existing_type=sa.UnicodeText(), type=sa.Unicode(150)
    )

"""Remove obsolete meeting attributes.

Revision ID: 9d4ba8cf710a
Revises: 65acbe9b0646
Create Date: 2022-08-12 15:43:01.721995
"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9d4ba8cf710a"
down_revision = "65acbe9b0646"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("meeting", "status")
    op.drop_column("meeting", "never_created")
    op.drop_column("meeting", "has_changed")
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "meeting",
        sa.Column("has_changed", sa.BOOLEAN(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "meeting",
        sa.Column("never_created", sa.BOOLEAN(), autoincrement=False, nullable=True),
    )
    op.add_column(
        "meeting", sa.Column("status", sa.BOOLEAN(), autoincrement=False, nullable=True)
    )
    # ### end Alembic commands ###

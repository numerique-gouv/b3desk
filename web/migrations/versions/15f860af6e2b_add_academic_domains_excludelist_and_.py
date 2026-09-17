"""add academic codes, mail_domains excludelist and user metadata.

Revision ID: 15f860af6e2b
Revises: a3203f74e042
Create Date: 2026-06-30 08:44:48.397024

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "15f860af6e2b"
down_revision = "a3203f74e042"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "excludelist",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"],
            ["group.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "group_id"),
    )
    with op.batch_alter_table("group", schema=None) as batch_op:
        batch_op.add_column(sa.Column("academic_codes", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("mail_domains", sa.JSON(), nullable=True))

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("meta_data", sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("meta_data")

    with op.batch_alter_table("group", schema=None) as batch_op:
        batch_op.drop_column("academic_codes")
        batch_op.drop_column("mail_domains")

    op.drop_table("excludelist")

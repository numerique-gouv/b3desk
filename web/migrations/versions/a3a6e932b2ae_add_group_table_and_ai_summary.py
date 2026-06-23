"""add group table and ai-summary.

Revision ID: a3a6e932b2ae
Revises: 791755877bb1
Create Date: 2026-06-23 12:11:52.642974

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3a6e932b2ae"
down_revision = "791755877bb1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "group",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("name", sa.Unicode(length=150), nullable=True),
        sa.Column("enable_sip", sa.Boolean(), nullable=True),
        sa.Column("enable_file_sharing", sa.Boolean(), nullable=True),
        sa.Column("enable_ai_summary", sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "group_member",
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
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "ai_summary",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("ai_summary")

    op.drop_table("group_member")
    op.drop_table("group")

"""add group table and ai-summary.

Replaces the ``meta_disable_recording_ai_summary`` column introduced by
``fd08854f3582`` with the ``ai_summary`` column (inverted semantics) and adds
the ``group`` and ``group_member`` tables.

Revision ID: a3a6e932b2ae
Revises: fd08854f3582
Create Date: 2026-06-23 12:11:52.642974

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3a6e932b2ae"
down_revision = "fd08854f3582"
branch_labels = None
depends_on = None


meeting_table = sa.table(
    "meeting",
    sa.column("ai_summary", sa.Boolean),
    sa.column("meta_disable_recording_ai_summary", sa.Boolean),
)


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

    op.execute(
        meeting_table.update().values(
            ai_summary=sa.not_(meeting_table.c.meta_disable_recording_ai_summary)
        )
    )

    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("meta_disable_recording_ai_summary")


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "meta_disable_recording_ai_summary",
                sa.Boolean(),
                nullable=False,
                server_default=sa.true(),
            )
        )

    op.execute(
        meeting_table.update().values(
            meta_disable_recording_ai_summary=sa.not_(meeting_table.c.ai_summary)
        )
    )

    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("ai_summary")

    op.drop_table("group_member")
    op.drop_table("group")

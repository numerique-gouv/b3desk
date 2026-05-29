"""group table.

Revision ID: 73ae59bac030
Revises: b32f0a8c28bd
Create Date: 2026-05-29 07:00:35.826831

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "73ae59bac030"
down_revision = "b32f0a8c28bd"
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
        sa.Column("enable_transcription", sa.Boolean(), nullable=True),
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

    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("admin", existing_type=sa.BOOLEAN(), nullable=True)


def downgrade():
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.alter_column("admin", existing_type=sa.BOOLEAN(), nullable=False)

    op.drop_table("group_member")
    op.drop_table("group")

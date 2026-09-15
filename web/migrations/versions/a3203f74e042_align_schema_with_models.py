"""align the schema with the models.

Revision ID: a3203f74e042
Revises: a84397b15b7f
Create Date: 2026-08-14 15:12:44.183920

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3203f74e042"
down_revision = "a84397b15b7f"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        # attendeePW and moderatorPW hold the base64 output of
        # StringEncryptedType, whose impl is String. They were created as
        # LargeBinary back when the models used EncryptedType. Without the
        # USING clause PostgreSQL stores the hexadecimal representation of the
        # bytes instead of decoding them, which would lose the ciphertext.
        batch_op.alter_column(
            "attendeePW",
            existing_type=sa.LargeBinary(),
            type_=sa.String(),
            existing_nullable=True,
            postgresql_using="convert_from(\"attendeePW\", 'UTF8')",
        )
        batch_op.alter_column(
            "moderatorPW",
            existing_type=sa.LargeBinary(),
            type_=sa.String(),
            existing_nullable=True,
            postgresql_using="convert_from(\"moderatorPW\", 'UTF8')",
        )
        # The server default only existed to backfill the column when it was
        # added as NOT NULL; the models declare a Python-side default instead.
        batch_op.alter_column(
            "ai_summary",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=None,
        )

    with op.batch_alter_table("meeting_files", schema=None) as batch_op:
        batch_op.alter_column("title", existing_type=sa.Unicode(4096), nullable=True)


def downgrade():
    with op.batch_alter_table("meeting_files", schema=None) as batch_op:
        batch_op.alter_column("title", existing_type=sa.Unicode(4096), nullable=False)

    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column(
            "ai_summary",
            existing_type=sa.Boolean(),
            existing_nullable=False,
            server_default=sa.false(),
        )
        batch_op.alter_column(
            "moderatorPW",
            existing_type=sa.String(),
            type_=sa.LargeBinary(),
            existing_nullable=True,
            postgresql_using="convert_to(\"moderatorPW\", 'UTF8')",
        )
        batch_op.alter_column(
            "attendeePW",
            existing_type=sa.String(),
            type_=sa.LargeBinary(),
            existing_nullable=True,
            postgresql_using="convert_to(\"attendeePW\", 'UTF8')",
        )

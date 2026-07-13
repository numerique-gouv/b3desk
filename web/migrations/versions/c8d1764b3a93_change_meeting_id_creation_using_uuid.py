"""change meeting.id creation using uuid.

Revision ID: c8d1764b3a93
Revises: a3a6e932b2ae
Create Date: 2026-07-10 10:22:03.638104

Downgrade is only safe if no meeting has been created since the upgrade:
meetings created after this migration get a UUID as ``id``, which cannot
be cast back to an integer. If any such meeting exists, the downgrade will
fail when Postgres tries to convert ``id`` back to Integer.
"""

import hashlib

import sqlalchemy as sa
from alembic import op
from b3desk.utils import secret_key
from sqlalchemy.orm import Session
from sqlalchemy.sql import select
from sqlalchemy.sql import update

# revision identifiers, used by Alembic.
revision = "c8d1764b3a93"
down_revision = "a3a6e932b2ae"
branch_labels = None
depends_on = None


def bbb_meeting_id_creation(id, owner_email):
    hash_ = hashlib.sha1(f"{owner_email}|{secret_key()}".encode()).hexdigest()
    return f"meeting-persistent-{id}--{hash_}"


def _drop_meeting_id_fks():
    with op.batch_alter_table("favorite", schema=None) as batch_op:
        batch_op.drop_constraint("favorite_meeting_id_fkey", type_="foreignkey")

    with op.batch_alter_table("meeting_access", schema=None) as batch_op:
        batch_op.drop_constraint("meeting_access_meeting_id_fkey", type_="foreignkey")

    with op.batch_alter_table("meeting_files", schema=None) as batch_op:
        batch_op.drop_constraint("meeting_files_meeting_id_fkey", type_="foreignkey")


def _create_meeting_id_fks():
    with op.batch_alter_table("favorite", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "favorite_meeting_id_fkey", "meeting", ["meeting_id"], ["id"]
        )

    with op.batch_alter_table("meeting_access", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "meeting_access_meeting_id_fkey", "meeting", ["meeting_id"], ["id"]
        )

    with op.batch_alter_table("meeting_files", schema=None) as batch_op:
        batch_op.create_foreign_key(
            "meeting_files_meeting_id_fkey", "meeting", ["meeting_id"], ["id"]
        )


def upgrade():
    is_postgresql = op.get_bind().dialect.name == "postgresql"

    if is_postgresql:
        _drop_meeting_id_fks()

    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("bbb_meeting_id", sa.String(length=255), nullable=True)
        )
        batch_op.alter_column(
            "id",
            existing_type=sa.INTEGER(),
            type_=sa.String(length=255),
            existing_nullable=False,
            existing_server_default=sa.text("nextval('meeting_id_seq'::regclass)"),
            server_default=None,
        )

    with op.batch_alter_table("favorite", schema=None) as batch_op:
        batch_op.alter_column(
            "meeting_id",
            existing_type=sa.INTEGER(),
            type_=sa.String(length=255),
            existing_nullable=False,
        )

    with op.batch_alter_table("meeting_access", schema=None) as batch_op:
        batch_op.alter_column(
            "meeting_id",
            existing_type=sa.INTEGER(),
            type_=sa.String(length=255),
            existing_nullable=False,
        )

    with op.batch_alter_table("meeting_files", schema=None) as batch_op:
        batch_op.alter_column(
            "title", existing_type=sa.VARCHAR(length=4096), nullable=True
        )
        batch_op.alter_column(
            "meeting_id",
            existing_type=sa.INTEGER(),
            type_=sa.String(length=255),
            existing_nullable=False,
        )

    if is_postgresql:
        _create_meeting_id_fks()

    bind = op.get_bind()
    session = Session(bind)
    meeting = sa.table(
        "meeting",
        sa.column("id", sa.Integer),
        sa.column("owner_id", sa.Integer),
        sa.column("bbb_meeting_id", sa.String),
    )
    user = sa.table("user", sa.column("id", sa.Integer), sa.column("email", sa.Unicode))

    for id, owner_id in session.execute(select(meeting.c.id, meeting.c.owner_id)):
        owner_email = session.execute(
            select(user.c.email).where(user.c.id == owner_id)
        ).scalar()
        session.execute(
            update(meeting)
            .where(meeting.c.id == id)
            .values(bbb_meeting_id=bbb_meeting_id_creation(id, owner_email))
        )
    session.commit()


def downgrade():
    is_postgresql = op.get_bind().dialect.name == "postgresql"

    if is_postgresql:
        _drop_meeting_id_fks()

    with op.batch_alter_table("meeting_files", schema=None) as batch_op:
        batch_op.alter_column(
            "meeting_id",
            existing_type=sa.String(length=255),
            type_=sa.INTEGER(),
            existing_nullable=False,
            postgresql_using="meeting_id::integer",
        )
        batch_op.alter_column(
            "title", existing_type=sa.VARCHAR(length=4096), nullable=False
        )

    with op.batch_alter_table("meeting_access", schema=None) as batch_op:
        batch_op.alter_column(
            "meeting_id",
            existing_type=sa.String(length=255),
            type_=sa.INTEGER(),
            existing_nullable=False,
            postgresql_using="meeting_id::integer",
        )

    with op.batch_alter_table("favorite", schema=None) as batch_op:
        batch_op.alter_column(
            "meeting_id",
            existing_type=sa.String(length=255),
            type_=sa.INTEGER(),
            existing_nullable=False,
            postgresql_using="meeting_id::integer",
        )

    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column(
            "id",
            existing_type=sa.String(length=255),
            type_=sa.INTEGER(),
            existing_nullable=False,
            existing_server_default=sa.text("nextval('meeting_id_seq'::regclass)"),
            postgresql_using="id::integer",
        )
        batch_op.drop_column("bbb_meeting_id")

    if is_postgresql:
        _create_meeting_id_fks()

"""save meeting secret keys and bbb_meeting_id.

Revision ID: a84397b15b7f
Revises: a3a6e932b2ae
Create Date: 2026-07-27 13:43:31.892476

"""

import hashlib
import uuid
from datetime import datetime

import sqlalchemy as sa
from alembic import op
from b3desk.models.meetings import Meeting
from flask import current_app
from sqlalchemy.sql import bindparam
from sqlalchemy.sql import insert
from sqlalchemy.sql import select
from sqlalchemy.sql import update

# revision identifiers, used by Alembic.
revision = "a84397b15b7f"
down_revision = "a3a6e932b2ae"
branch_labels = None
depends_on = None

ROLES = ("attendee", "moderator", "authenticated")
BATCH_SIZE = 5000


def legacy_bbb_meeting_id(meeting_id, owner_email, app_secret_key):
    """Rebuild the BBB meeting id the previous code computed on the fly."""
    owner_hash = (
        hashlib.sha1(f"{owner_email}|{app_secret_key}".encode()).hexdigest()
        if owner_email
        else ""
    )
    return f"meeting-persistent-{meeting_id}--{owner_hash}"


def legacy_secret_keys(bbb_meeting_id, attendee_pw, name, role):
    """Rebuild the hashes of the signin links already handed out, in both role spellings."""
    return [
        hashlib.sha1(
            f"{bbb_meeting_id}|{attendee_pw}|{name}|{spelling}".encode()
        ).hexdigest()
        for spelling in (f"Role.{role}", role)
    ]


def upgrade():
    op.create_table(
        "meeting_secret_key",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=255), nullable=True),
        sa.Column("secret_key", sa.String(length=255), nullable=False),
        sa.Column("legacy_secret_keys", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meeting.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "role"),
        sa.UniqueConstraint("secret_key"),
    )
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("bbb_meeting_id", sa.String(length=255), nullable=True)
        )

    meeting = sa.table(
        "meeting",
        sa.column("id", sa.Integer),
        sa.column("name", sa.Unicode),
        sa.column("attendeePW", Meeting.__table__.c.attendeePW.type),
        sa.column("owner_id", sa.Integer),
        sa.column("bbb_meeting_id", sa.String),
    )
    user = sa.table("user", sa.column("id", sa.Integer), sa.column("email", sa.String))
    meeting_secret_key = sa.table(
        "meeting_secret_key",
        sa.column("meeting_id", sa.Integer),
        sa.column("role", sa.String),
        sa.column("secret_key", sa.String),
        sa.column("legacy_secret_keys", sa.JSON),
        sa.column("created_at", sa.DateTime),
        sa.column("updated_at", sa.DateTime),
    )

    connection = op.get_bind()
    now = datetime.now()
    last_id = 0
    while rows := connection.execute(
        select(meeting.c.id, meeting.c.name, meeting.c.attendeePW, user.c.email)
        .select_from(meeting.outerjoin(user, meeting.c.owner_id == user.c.id))
        .where(meeting.c.id > last_id)
        .order_by(meeting.c.id)
        .limit(BATCH_SIZE)
    ).all():
        meeting_values = []
        secret_key_values = []
        for meeting_id, name, attendee_pw, owner_email in rows:
            bbb_meeting_id = legacy_bbb_meeting_id(
                meeting_id, owner_email, current_app.config["SECRET_KEY"]
            )
            name = name or str(current_app.config["QUICK_MEETING_DEFAULT_NAME"])
            meeting_values.append(
                {"_id": meeting_id, "_bbb_meeting_id": bbb_meeting_id}
            )
            secret_key_values.extend(
                {
                    "meeting_id": meeting_id,
                    "role": role,
                    "secret_key": str(uuid.uuid7()),
                    "legacy_secret_keys": legacy_secret_keys(
                        bbb_meeting_id, attendee_pw, name, role
                    ),
                    "created_at": now,
                    "updated_at": now,
                }
                for role in ROLES
            )

        connection.execute(
            update(meeting)
            .where(meeting.c.id == bindparam("_id"))
            .values(bbb_meeting_id=bindparam("_bbb_meeting_id")),
            meeting_values,
        )
        connection.execute(insert(meeting_secret_key), secret_key_values)
        last_id = rows[-1][0]

    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.alter_column(
            "bbb_meeting_id", existing_type=sa.String(length=255), nullable=False
        )
        batch_op.create_unique_constraint(
            "uq_meeting_bbb_meeting_id", ["bbb_meeting_id"]
        )


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("bbb_meeting_id")

    op.drop_table("meeting_secret_key")

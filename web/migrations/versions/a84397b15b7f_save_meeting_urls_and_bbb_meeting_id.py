"""save meeting urls and bbb_meeting_id.

Revision ID: a84397b15b7f
Revises: a3a6e932b2ae
Create Date: 2026-07-27 13:43:31.892476

"""

import hashlib

import sqlalchemy as sa
from alembic import op
from b3desk.join import create_signin_url
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingUrls
from b3desk.models.roles import Role
from b3desk.utils import secret_key
from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload

# revision identifiers, used by Alembic.
revision = "a84397b15b7f"
down_revision = "a3a6e932b2ae"
branch_labels = None
depends_on = None


def bbb_meeting_id_creation(id, owner_email):
    hash_ = hashlib.sha1(f"{owner_email}|{secret_key()}".encode()).hexdigest()
    return f"meeting-persistent-{id}--{hash_}"


def upgrade():
    op.create_table(
        "meeting_urls",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("meeting_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=4096), nullable=True),
        sa.Column("role", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["meeting_id"],
            ["meeting.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("meeting_id", "role"),
    )
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("bbb_meeting_id", sa.String(length=255), nullable=True)
        )
        batch_op.create_unique_constraint(
            "uq_meeting_bbb_meeting_id", ["bbb_meeting_id"]
        )

    bind = op.get_bind()
    session = Session(bind)

    for meeting in session.query(Meeting).options(joinedload(Meeting.owner)):
        meeting.bbb_meeting_id = bbb_meeting_id_creation(
            meeting.id, meeting.owner.email
        )
        for role in Role:
            session.add(
                MeetingUrls(
                    meeting_id=meeting.id,
                    role=role.name,
                    url=create_signin_url(meeting, role),
                )
            )
    session.commit()


def downgrade():
    with op.batch_alter_table("meeting", schema=None) as batch_op:
        batch_op.drop_column("bbb_meeting_id")

    op.drop_table("meeting_urls")

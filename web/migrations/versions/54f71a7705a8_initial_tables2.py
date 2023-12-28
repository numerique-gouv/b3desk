"""Initial tables2.

Revision ID: 54f71a7705a8
Revises:
Create Date: 2023-01-03 18:01:03.770238
"""
import os
import sys

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

import alembic_helpers

# alembic_helpers = imp.load_source('alembic_helpers', (
#    os.getcwd() + '/' + op.get_context().script.dir + '/alembic_helpers.py'))

# revision identifiers, used by Alembic.
revision = "54f71a7705a8"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    if alembic_helpers.table_does_not_exist("user"):
        op.create_table(
            "user",
            sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
            sa.Column(
                "email", sa.VARCHAR(length=150), autoincrement=False, nullable=True
            ),
            sa.Column(
                "given_name", sa.VARCHAR(length=50), autoincrement=False, nullable=True
            ),
            sa.Column(
                "family_name", sa.VARCHAR(length=50), autoincrement=False, nullable=True
            ),
            sa.PrimaryKeyConstraint("id", name="user_pkey"),
            sa.UniqueConstraint("email", name="user_email_key"),
        )

    if alembic_helpers.table_does_not_exist("meeting"):
        op.create_table(
            "meeting",
            sa.Column(
                "id",
                sa.INTEGER(),
                server_default=sa.text("nextval('meeting_id_seq'::regclass)"),
                autoincrement=True,
                nullable=False,
            ),
            sa.Column(
                "name", sa.VARCHAR(length=150), autoincrement=False, nullable=True
            ),
            sa.Column(
                "attendeePW", postgresql.BYTEA(), autoincrement=False, nullable=True
            ),
            sa.Column(
                "moderatorPW", postgresql.BYTEA(), autoincrement=False, nullable=True
            ),
            sa.Column("welcome", sa.TEXT(), autoincrement=False, nullable=True),
            sa.Column(
                "dialNumber", sa.VARCHAR(length=50), autoincrement=False, nullable=True
            ),
            sa.Column(
                "voiceBridge", sa.VARCHAR(length=50), autoincrement=False, nullable=True
            ),
            sa.Column(
                "maxParticipants", sa.INTEGER(), autoincrement=False, nullable=True
            ),
            sa.Column(
                "logoutUrl", sa.VARCHAR(length=250), autoincrement=False, nullable=True
            ),
            sa.Column("record", sa.BOOLEAN(), autoincrement=False, nullable=True),
            sa.Column("duration", sa.INTEGER(), autoincrement=False, nullable=True),
            sa.Column(
                "moderatorOnlyMessage",
                sa.VARCHAR(length=150),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column(
                "autoStartRecording", sa.BOOLEAN(), autoincrement=False, nullable=True
            ),
            sa.Column(
                "allowStartStopRecording",
                sa.BOOLEAN(),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column(
                "webcamsOnlyForModerator",
                sa.BOOLEAN(),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column("muteOnStart", sa.BOOLEAN(), autoincrement=False, nullable=True),
            sa.Column(
                "lockSettingsDisableCam",
                sa.BOOLEAN(),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column(
                "lockSettingsDisableMic",
                sa.BOOLEAN(),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column(
                "allowModsToUnmuteUsers",
                sa.BOOLEAN(),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column(
                "lockSettingsDisablePrivateChat",
                sa.BOOLEAN(),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column(
                "lockSettingsDisablePublicChat",
                sa.BOOLEAN(),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column(
                "lockSettingsDisableNote",
                sa.BOOLEAN(),
                autoincrement=False,
                nullable=True,
            ),
            sa.Column(
                "logo", sa.VARCHAR(length=200), autoincrement=False, nullable=True
            ),
            sa.Column("status", sa.BOOLEAN(), autoincrement=False, nullable=True),
            sa.Column(
                "never_created", sa.BOOLEAN(), autoincrement=False, nullable=True
            ),
            sa.Column("has_changed", sa.BOOLEAN(), autoincrement=False, nullable=True),
            sa.Column("user_id", sa.INTEGER(), autoincrement=False, nullable=False),
            sa.ForeignKeyConstraint(
                ["user_id"], ["user.id"], name="meeting_user_id_fkey"
            ),
            sa.PrimaryKeyConstraint("id", name="meeting_pkey"),
            postgresql_ignore_search_path=False,
        )


def downgrade():
    op.drop_table("user")
    op.drop_table("meeting")

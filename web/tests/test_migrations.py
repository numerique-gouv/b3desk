from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
from b3desk.models import db
from b3desk.models.meetings import Meeting
from flask_migrate import downgrade
from flask_migrate import upgrade
from migrations.versions.c8d1764b3a93_change_meeting_id_creation_using_uuid_and_save_meeting_urls import (
    bbb_meeting_id_creation,
)

MIGRATIONS_DIR = str(Path(__file__).parent.parent / "migrations")


def test_migrations(app):
    """Test applying all migrations, downgrade to base, then upgrade again."""
    with app.app_context():
        downgrade(directory=MIGRATIONS_DIR, revision="base")
        upgrade(directory=MIGRATIONS_DIR)


def test_migration_uuid_for_meetings(app):
    """Meetings created before the UUID migration get a bbb_meeting_id derived from their old integer id."""
    with app.app_context():
        downgrade(directory=MIGRATIONS_DIR, revision="a3a6e932b2ae")

        metadata = sa.MetaData()
        user = sa.Table(
            "user",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("email", sa.Unicode),
            sa.Column("created_at", sa.DateTime),
            sa.Column("admin", sa.Boolean),
        )
        meeting = sa.Table(
            "meeting",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("owner_id", sa.Integer),
            sa.Column("created_at", sa.DateTime),
            sa.Column("updated_at", sa.DateTime),
            sa.Column("visio_code", sa.Unicode),
            sa.Column("voiceBridge", sa.Unicode),
            sa.Column("ai_summary", sa.Boolean),
        )

        now = datetime.now()
        owner_email = "owner@domain.test"
        owner_id = db.session.execute(
            sa.insert(user).values(email=owner_email, created_at=now, admin=False)
        ).inserted_primary_key[0]
        meeting_id = db.session.execute(
            sa.insert(meeting).values(
                id=1,
                owner_id=owner_id,
                created_at=now,
                updated_at=now,
                visio_code="migration-test-code",
                voiceBridge="199999999",
                ai_summary=False,
            )
        ).inserted_primary_key[0]
        db.session.commit()

        upgrade(directory=MIGRATIONS_DIR, revision="c8d1764b3a93")

        migrated_meeting = db.session.get(Meeting, str(meeting_id))
        assert migrated_meeting.bbb_meeting_id == bbb_meeting_id_creation(
            meeting_id, owner_email
        )

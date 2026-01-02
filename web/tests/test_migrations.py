from pathlib import Path

import pytest
from b3desk.models import db
from flask import Flask
from flask_migrate import Migrate
from flask_migrate import downgrade
from flask_migrate import upgrade

MIGRATIONS_DIR = str(Path(__file__).parent.parent / "migrations")


@pytest.fixture
def migration_app(postgresql_db):
    """Minimal Flask app for migration testing."""
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = postgresql_db
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    with app.app_context():
        db.drop_all()
        db.session.execute(db.text("DROP TABLE IF EXISTS alembic_version"))
        db.session.commit()
        Migrate(app, db, compare_type=True, directory=MIGRATIONS_DIR)

    return app


def test_migrations(migration_app):
    """Test applying all migrations, downgrade to base, then upgrade again."""
    with migration_app.app_context():
        upgrade(directory=MIGRATIONS_DIR)
        downgrade(directory=MIGRATIONS_DIR, revision="base")
        upgrade(directory=MIGRATIONS_DIR)

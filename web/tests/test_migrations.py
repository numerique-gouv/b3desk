from pathlib import Path

from flask_migrate import downgrade
from flask_migrate import upgrade

MIGRATIONS_DIR = str(Path(__file__).parent.parent / "migrations")


def test_migrations(app):
    """Test applying all migrations, downgrade to base, then upgrade again."""
    with app.app_context():
        downgrade(directory=MIGRATIONS_DIR, revision="base")
        upgrade(directory=MIGRATIONS_DIR)


def test_create_favorite_table(app, user, meeting):
    """Test migrations, downgrade to a1b2c3d4e5f6, then upgrade again for creating favorite_meetings table with values."""
    with app.app_context():
        downgrade(directory=MIGRATIONS_DIR, revision="a1b2c3d4e5f6")
        upgrade(directory=MIGRATIONS_DIR)

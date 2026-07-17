from pathlib import Path

from flask_migrate import downgrade
from flask_migrate import upgrade

MIGRATIONS_DIR = str(Path(__file__).parent.parent / "migrations")


def test_migrations(app):
    """Test applying all migrations, downgrade to base, then upgrade again."""
    with app.app_context():
        downgrade(directory=MIGRATIONS_DIR, revision="base")
        upgrade(directory=MIGRATIONS_DIR)

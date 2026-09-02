"""Point d'entrée des services Celery.

Construit l'application Flask, qui instancie et configure l'application Celery,
puis expose cette dernière. Utilisé via ``celery --app b3desk.celery_worker
worker`` et ``celery --app b3desk.celery_worker beat``.
"""

from celery.signals import worker_process_init

from b3desk import create_app
from b3desk.models import db

flask_app = create_app()
celery_app = flask_app.extensions["celery"]


@worker_process_init.connect
def reset_database_pool(**kwargs):
    """Give each forked worker process its own connection pool."""
    with flask_app.app_context():
        db.engine.dispose(close=False)


__all__ = ["celery_app", "flask_app"]

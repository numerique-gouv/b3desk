"""Point d'entrée du worker Celery.

Construit l'application Flask (et donc applique ``ContextTask`` sur
l'instance Celery) avant que le worker n'accepte des tâches.
Utilisé via ``celery --app b3desk.celery_worker.celery worker``.
"""

from b3desk import create_app
from b3desk.tasks import celery

flask_app = create_app()

__all__ = ["celery", "flask_app"]

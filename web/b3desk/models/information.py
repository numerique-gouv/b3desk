# +----------------------------------------------------------------------------+
# | B3DESK                                                                  |
# +----------------------------------------------------------------------------+
#
#   This program is free software: you can redistribute it and/or modify it
# under the terms of the European Union Public License 1.2 version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.
"""Shared warning sequence used by both Meeting and User."""

from datetime import timedelta

from sqlalchemy import and_

from b3desk.utils.mailing import DELAY_FOR_THIRD_EMAIL
from b3desk.utils.mailing import EMAIL_DELAYS

from . import db


def compute_first_mail_deadline(now, inactivity_period):
    """Activity older than this deadline means the first warning mail is due."""
    return now - inactivity_period + timedelta(days=EMAIL_DELAYS[0])


def ready_for_final_deletion(model, now):
    """SQLAlchemy condition: last warning mail sent and its grace period elapsed."""
    grace_deadline = now - timedelta(days=DELAY_FOR_THIRD_EMAIL)
    return and_(
        model.information_level == len(EMAIL_DELAYS),
        model.information_sent_at < grace_deadline,
    )


def get_entities_due_for_next_mail(model, now, extra_filter=True):
    """Return (entity, delay, new_level) for entities due for their next warning mail."""
    entities = []
    for level in range(1, len(EMAIL_DELAYS)):
        previous_delay = EMAIL_DELAYS[level - 1]
        next_delay = EMAIL_DELAYS[level]
        wait = timedelta(days=previous_delay - next_delay)
        due = db.session.scalars(
            db.select(model).where(
                model.information_level == level,
                model.information_sent_at <= now - wait,
                extra_filter,
            )
        ).all()
        entities += [(entity, next_delay, level + 1) for entity in due]
    return entities

from functools import wraps

from flask import abort
from flask import current_app
from flask import g
from flask import session
from flask_pyoidc.user_session import UserSession


def has_user_session():
    """Check if user has an active authenticated session."""
    user_session = UserSession(dict(session), "default")
    return user_session.is_authenticated()


def get_authenticated_attendee_fullname():
    """Extract and return full name from authenticated attendee session."""
    attendee_session = UserSession(session)
    attendee_info = attendee_session.userinfo
    given_name = attendee_info.get("given_name", "").title()
    family_name = attendee_info.get("family_name", "").title()
    fullname = f"{given_name} {family_name}".strip()
    return fullname


def user_needed(view_function):
    """Require that an authenticated user is present."""

    @wraps(view_function)
    def decorator(*args, **kwargs):
        if not has_user_session() or not g.user:
            abort(403)

        return view_function(*args, user=g.user, **kwargs)

    return decorator


def meeting_access_required(level=None):
    """Require that the user owns the meeting or has at least the given access level."""
    from b3desk.models import db
    from b3desk.models.meetings import Meeting
    from b3desk.models.meetings import MeetingAccess

    def wrapper(view_function):
        @wraps(view_function)
        def decorator(*args, meeting, **kwargs):
            if not g.user:
                abort(403)

            meeting = db.session.get(Meeting, meeting.id)

            if meeting.owner == g.user:
                return view_function(*args, user=g.user, meeting=meeting, **kwargs)

            if level is not None:
                access = MeetingAccess.query.filter_by(
                    user_id=g.user.id, meeting_id=meeting.id
                ).one_or_none()
                if access and access.level >= level:
                    return view_function(*args, user=g.user, meeting=meeting, **kwargs)

            abort(403)

        return decorator

    return wrapper


def visio_code_attempt_counter_increment():
    """Increment the visio code attempt counter in session."""
    visio_code_attempt_counter = session.setdefault("visio_code_attempt_counter", 0)
    session["visio_code_attempt_counter"] = visio_code_attempt_counter + 1


def visio_code_attempt_counter_reset():
    """Reset the visio code attempt counter in session."""
    session.pop("visio_code_attempt_counter", None)


def should_display_captcha(check_service_status=True):
    """Determine if CAPTCHA should be displayed based on attempt count and configuration."""
    from b3desk.endpoints.captcha import captcha_error
    from b3desk.endpoints.captcha import captchetat_service_status

    if (
        not current_app.config["PISTE_OAUTH_CLIENT_ID"]
        or not current_app.config["PISTE_OAUTH_CLIENT_SECRET"]
        or not current_app.config["CAPTCHETAT_API_URL"]
        or not current_app.config["PISTE_OAUTH_API_URL"]
    ):
        return False

    if session.get("visio_code_attempt_counter", 0) <= current_app.config.get(
        "CAPTCHA_NUMBER_ATTEMPTS"
    ):
        return False

    # hotfix until the captchetat js lib allow custom handling of errors
    # When it is done, we can just hide the captcha in the front if
    # something happened, and avoid perform a healthcheck query here.
    # https://gitlab.adullact.net/captchetat/client-libraries/js/-/issues/4
    if check_service_status and captchetat_service_status() != "UP":
        captcha_error("Captchetat service is down")
        return False

    return True

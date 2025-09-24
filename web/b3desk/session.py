from functools import wraps

from flask import abort
from flask import current_app
from flask import g
from flask import session
from flask_pyoidc.user_session import UserSession

from b3desk.models.users import get_or_create_user


def get_current_user():
    if "user" not in g:
        user_session = UserSession(session)
        info = user_session.userinfo
        g.user = get_or_create_user(info)
        current_app.logger.debug(
            f"User authenticated with token: {user_session.access_token}"
        )
    return g.user


def has_user_session():
    user_session = UserSession(dict(session), "default")
    return user_session.is_authenticated()


def get_authenticated_attendee_fullname():
    attendee_session = UserSession(session)
    attendee_info = attendee_session.userinfo
    given_name = attendee_info.get("given_name", "").title()
    family_name = attendee_info.get("family_name", "").title()
    fullname = f"{given_name} {family_name}".strip()
    return fullname


def meeting_owner_needed(view_function):
    @wraps(view_function)
    def decorator(*args, **kwargs):
        if not has_user_session():
            abort(403)

        user = get_current_user()
        if not user or kwargs["meeting"].user != user:
            abort(403)

        return view_function(*args, owner=user, **kwargs)

    return decorator


def visio_code_attempt_counter_increment():
    visio_code_attempt_counter = session.setdefault("visio_code_attempt_counter", 0)
    session["visio_code_attempt_counter"] = visio_code_attempt_counter + 1


def visio_code_attempt_counter_reset():
    session.pop("visio_code_attempt_counter", None)


def should_display_captcha(check_service_status=True):
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

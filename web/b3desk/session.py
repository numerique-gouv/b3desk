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

from b3desk.models.users import get_or_create_user
from flask import session
from flask_pyoidc.user_session import UserSession


def get_current_user():
    user_session = UserSession(session)
    info = user_session.userinfo
    return get_or_create_user(info)


def has_user_session():
    user_session = UserSession(dict(session), "default")
    return user_session.is_authenticated()


def get_authenticated_attendee_fullname():
    attendee_session = UserSession(session)
    attendee_info = attendee_session.userinfo
    given_name = attendee_info.get("given_name", "")
    family_name = attendee_info.get("family_name", "")
    fullname = f"{given_name} {family_name}".strip()
    return fullname

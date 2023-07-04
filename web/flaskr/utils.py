from flask import current_app


def secret_key():
    return current_app.config["SECRET_KEY"]


def retry_join_meeting(referrer, role, fullname, fullname_suffix):
    return bool(
        (referrer and "/meeting/wait/" in referrer)
        or (role in ("attendee", "moderator") and fullname)
        or (role == "authenticated" and fullname and fullname_suffix)
    )

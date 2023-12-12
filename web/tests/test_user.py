from datetime import date

from b3desk.models import get_or_create_user
from b3desk.models import User
from freezegun import freeze_time


def test_get_or_create_user(client_app):
    user_info = {
        "given_name": "Alice",
        "family_name": "Cooper",
        "preferred_username": "alice",
        "email": "alice@mydomain.test",
    }
    get_or_create_user(user_info)

    user = User.query.get(1)
    assert user.given_name == "Alice"
    assert user.family_name == "Cooper"
    assert user.email == "alice@mydomain.test"
    assert user.last_connection_utc_datetime.date() == date.today()


def test_update_last_connection_if_more_than_24h(client_app):
    user_info = {
        "given_name": "Alice",
        "family_name": "Cooper",
        "preferred_username": "alice",
        "email": "alice@mydomain.test",
    }
    with freeze_time("2021-08-10"):
        get_or_create_user(user_info)

    with freeze_time("2021-08-11"):
        user = User.query.get(1)
        assert user.last_connection_utc_datetime.date() == date(2021, 8, 10)

        get_or_create_user(user_info)

        assert user.last_connection_utc_datetime.date() == date(2021, 8, 11)

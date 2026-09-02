import datetime
from datetime import date

import pytest
import requests
from b3desk.models import db
from b3desk.models.meetings import MeetingFiles
from b3desk.models.users import User
from b3desk.models.users import get_inactive_users_to_inform
from b3desk.models.users import get_or_create_user
from b3desk.nextcloud import NoUserFound
from b3desk.nextcloud import TooManyUsers
from b3desk.nextcloud import get_secondary_identity_provider_id_from_email
from b3desk.nextcloud import get_user_nc_credentials
from b3desk.nextcloud import make_nextcloud_credentials_request
from b3desk.tasks import delete_old_users
from b3desk.tasks import inform_user_before_account_deletion
from b3desk.utils.mailing import DELAY_FOR_FIRST_EMAIL
from b3desk.utils.mailing import DELAY_FOR_SECOND_EMAIL
from b3desk.utils.mailing import DELAY_FOR_THIRD_EMAIL
from time_machine import travel


def test_get_or_create_user(client_app):
    """Test that user is created from user info."""
    assert db.session.get(User, 1) is None

    user_info = {
        "given_name": "Alice",
        "family_name": "Cooper",
        "preferred_username": "alice",
        "email": "alice@mydomain.test",
    }
    get_or_create_user(user_info)

    user = db.session.get(User, 1)
    assert user.given_name == "Alice"
    assert user.family_name == "Cooper"
    assert user.email == "alice@mydomain.test"
    assert user.last_connection_utc_datetime.date() == date.today()
    assert user.created_at.date() == date.today()


def test_update_last_connection_if_more_than_24h(client_app):
    """Test that last connection date updates after 24 hours."""
    user_info = {
        "given_name": "Alice",
        "family_name": "Cooper",
        "preferred_username": "alice",
        "email": "alice@mydomain.test",
    }
    with travel("2021-08-10 12:00:00"):
        get_or_create_user(user_info)

    with travel("2021-08-11 12:00:00"):
        user = db.session.get(User, 1)
        assert user.last_connection_utc_datetime.date() == date(2021, 8, 10)

        get_or_create_user(user_info)

    assert user.last_connection_utc_datetime.date() == date(2021, 8, 11)
    assert user.created_at.date() == date(2021, 8, 10)


def test_make_nextcloud_credentials_request_with_scheme_response(
    client_app, app, cloud_service_response, mocker
):
    """Test that Nextcloud credentials request preserves HTTP scheme."""
    assert cloud_service_response.data["nclocator"].startswith("http://")
    mocker.patch("b3desk.nextcloud.requests.post", return_value=cloud_service_response)
    app.config["FORCE_HTTPS_ON_EXTERNAL_URLS"] = False
    credentials = make_nextcloud_credentials_request(
        url=app.config["NC_LOGIN_API_URL"],
        payload={"username": "Alice"},
        headers={"X-API-KEY": app.config["NC_LOGIN_API_KEY"]},
    )
    assert credentials["nclocator"].startswith("http://")


@pytest.mark.secure
def test_make_nextcloud_credentials_request_with_secure_response(
    client_app, app, cloud_service_response, mocker
):
    """Test that Nextcloud credentials request preserves HTTPS scheme."""
    assert cloud_service_response.data["nclocator"].startswith("https://")
    mocker.patch("b3desk.nextcloud.requests.post", return_value=cloud_service_response)
    app.config["FORCE_HTTPS_ON_EXTERNAL_URLS"] = False
    credentials = make_nextcloud_credentials_request(
        url=app.config["NC_LOGIN_API_URL"],
        payload={"username": "Alice"},
        headers={"X-API-KEY": app.config["NC_LOGIN_API_KEY"]},
    )
    assert credentials["nclocator"].startswith("https://")


def test_make_nextcloud_credentials_request_force_secure_for_unsecure(
    client_app, app, cloud_service_response, mocker
):
    """Test that HTTP URLs are forced to HTTPS when configured."""
    assert cloud_service_response.data["nclocator"].startswith("http://")
    mocker.patch("b3desk.nextcloud.requests.post", return_value=cloud_service_response)
    app.config["FORCE_HTTPS_ON_EXTERNAL_URLS"] = True
    credentials = make_nextcloud_credentials_request(
        url=app.config["NC_LOGIN_API_URL"],
        payload={"username": "Alice"},
        headers={"X-API-KEY": app.config["NC_LOGIN_API_KEY"]},
    )
    assert credentials["nclocator"].startswith("https://")


@pytest.mark.no_scheme
def test_make_nextcloud_credentials_request_force_secure_for_missing_scheme(
    client_app, app, cloud_service_response, mocker
):
    """Test that missing scheme is forced to HTTPS when configured."""
    assert not cloud_service_response.data["nclocator"].startswith("http")
    mocker.patch("b3desk.nextcloud.requests.post", return_value=cloud_service_response)
    app.config["FORCE_HTTPS_ON_EXTERNAL_URLS"] = True
    credentials = make_nextcloud_credentials_request(
        url=app.config["NC_LOGIN_API_URL"],
        payload={"username": "Alice"},
        headers={"X-API-KEY": app.config["NC_LOGIN_API_KEY"]},
    )
    assert credentials["nclocator"].startswith("https://")


def test_get_secondary_identity_provider_id_from_email_token_error(
    client_app, mocker, caplog
):
    """Test that token error is logged when getting secondary identity provider ID."""

    class TokenErrorAnswer:
        text = "Unable to get token"

        def raise_for_status():
            raise requests.exceptions.HTTPError

    mocker.patch(
        "b3desk.nextcloud.get_secondary_identity_provider_token",
        return_value=TokenErrorAnswer,
    )
    with pytest.raises(requests.exceptions.HTTPError):
        get_secondary_identity_provider_id_from_email("jean.espece@rock.test")
    assert "Get token request error:" in caplog.text


def test_get_secondary_identity_provider_id_from_email_request_error(
    client_app, mocker, caplog, valid_secondary_identity_token
):
    """Test that request error is logged when getting secondary identity provider ID."""

    class RequestErrorAnswer:
        text = "Unable to ask identity provider"

        def raise_for_status():
            raise requests.exceptions.HTTPError

    mocker.patch(
        "b3desk.nextcloud.get_secondary_identity_provider_users_from_email",
        return_value=RequestErrorAnswer,
    )
    with pytest.raises(requests.exceptions.HTTPError):
        get_secondary_identity_provider_id_from_email("michel.vendeur@rock.test")
    assert "Get user from email request error:" in caplog.text


def test_get_secondary_identity_provider_id_from_email_many_users(
    client_app, app, mocker, valid_secondary_identity_token
):
    """Test that TooManyUsers exception is raised when multiple users found."""

    class ManyUsersAnswer:
        def raise_for_status():
            pass

        def json():
            return [{"username": "freddy"}, {"username": "fred"}]

    mocker.patch(
        "b3desk.nextcloud.get_secondary_identity_provider_users_from_email",
        return_value=ManyUsersAnswer,
    )
    with pytest.raises(TooManyUsers):
        get_secondary_identity_provider_id_from_email("frederick.mercure@rock.test")


def test_get_secondary_identity_provider_id_from_email_no_user(
    client_app, app, mocker, valid_secondary_identity_token
):
    """Test that NoUserFound exception is raised when no user found."""

    class NoUsersAnswer:
        def raise_for_status():
            pass

        def json():
            return []

    mocker.patch(
        "b3desk.nextcloud.get_secondary_identity_provider_users_from_email",
        return_value=NoUsersAnswer,
    )
    with pytest.raises(NoUserFound):
        get_secondary_identity_provider_id_from_email("blaireau.riviere@rock.test")


def test_get_user_nc_credentials_with_nextcloud_credentials_request_failed(
    client_app, user, mocker, caplog
):
    ncresponse = {
        "error": "test_nc_error_connection",
    }
    mocker.patch(
        "b3desk.nextcloud.make_nextcloud_credentials_request", return_value=ncresponse
    )
    response = get_user_nc_credentials(user)
    assert response == {"nctoken": None, "nclocator": None, "nclogin": None}
    assert (
        f"Cannot contact NC {client_app.app.config['NC_LOGIN_API_URL']}, returning error {ncresponse['error']}"
    ) in caplog.text


def test_delete_old_users(
    app,
    client_app,
    user,
    user_2,
    meeting,
    meeting_1_user_2,
    group,
    time_machine,
    bbb_getRecordings_response,
):
    group.members.append(user)
    user.last_connection_utc_datetime = datetime.datetime(2024, 1, 1)
    user.created_at = datetime.datetime(2024, 1, 1)
    user_2.last_connection_utc_datetime = datetime.datetime(2025, 1, 1)
    user_2.created_at = datetime.datetime(2025, 1, 1)
    meeting.last_connection_utc_datetime = datetime.datetime(2024, 1, 1)
    meeting.created_at = datetime.datetime(2024, 1, 1)
    meeting_1_user_2.last_connection_utc_datetime = datetime.datetime(2025, 1, 1)
    meeting_1_user_2.created_at = datetime.datetime(2025, 1, 1)

    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=meeting_1_user_2.id,
        owner=user,
    )
    db.session.add(meeting_file)
    db.session.commit()
    meeting_file_id = meeting_file.id

    time_machine.move_to(datetime.datetime(2025, 6, 1))
    delete_old_users()

    assert not db.session.get(User, 1)
    assert db.session.get(User, 2)
    assert not db.session.scalars(
        db.select(MeetingFiles).where(MeetingFiles.id == meeting_file_id)
    ).first()


def test_delete_old_users_no_action(app, client_app, caplog):
    """Test the cron task logs when there is no user to delete."""
    delete_old_users()
    assert "Celery cron task: no action required" in caplog.text


def test_delete_old_users_deletion_failure(app, client_app, user, mocker, caplog):
    """Test the cron task logs an error when a user could not be deleted."""
    user.last_connection_utc_datetime = datetime.datetime(2000, 1, 1)
    user.created_at = datetime.datetime(2000, 1, 1)
    db.session.commit()
    mocker.patch("b3desk.tasks.clean_db_and_delete_user", return_value=False)

    delete_old_users()

    assert (
        f"Celery cron task: user not deleted: {user.fullname}, id {user.id}, email {user.email}"
        in caplog.text
    )


def test_inform_user_before_account_deletion_no_action(app, client_app, caplog):
    """Test the cron task logs when there is no user to inform."""
    inform_user_before_account_deletion()
    assert "Celery cron task: no action required" in caplog.text


def test_inform_user_before_account_deletion(
    app,
    client_app,
    time_machine,
    user,
    user_2,
    user_3,
    smtpd,
):
    """Test user receives a mail before account deletion."""
    assert len(smtpd.messages) == 0
    test_date = datetime.datetime(2024, 1, 1)
    third_mail_date = (
        test_date
        - datetime.timedelta(
            days=client_app.app.config["INACTIVITY_TIMER_CLEANUP_ACCOUNT"]
        )
        + datetime.timedelta(days=DELAY_FOR_THIRD_EMAIL)
    )
    second_mail_date = (
        test_date
        - datetime.timedelta(
            days=client_app.app.config["INACTIVITY_TIMER_CLEANUP_ACCOUNT"]
        )
        + datetime.timedelta(days=DELAY_FOR_SECOND_EMAIL)
    )
    first_mail_date = (
        test_date
        - datetime.timedelta(
            days=client_app.app.config["INACTIVITY_TIMER_CLEANUP_ACCOUNT"]
        )
        + datetime.timedelta(days=DELAY_FOR_FIRST_EMAIL)
    )

    user.last_connection_utc_datetime = third_mail_date
    user.created_at = third_mail_date
    user_2.last_connection_utc_datetime = second_mail_date
    user_2.created_at = second_mail_date
    user_3.last_connection_utc_datetime = first_mail_date
    user_3.created_at = first_mail_date
    db.session.commit()

    time_machine.move_to(test_date)
    inform_user_before_account_deletion()
    users_to_inform = get_inactive_users_to_inform()
    assert users_to_inform == [
        (user_3, DELAY_FOR_FIRST_EMAIL),
        (user_2, DELAY_FOR_SECOND_EMAIL),
        (user, DELAY_FOR_THIRD_EMAIL),
    ]
    assert len(smtpd.messages) == 3


def test_inform_user_before_account_deletion_with_recently_used_meeting(
    app,
    client_app,
    time_machine,
    user,
    user_2,
    meeting,
    smtpd,
):
    """A recently used meeting postpones a user's account-deletion reminder."""
    assert len(smtpd.messages) == 0
    test_date = datetime.datetime(2024, 1, 1)
    first_mail_date = (
        test_date
        - datetime.timedelta(
            days=client_app.app.config["INACTIVITY_TIMER_CLEANUP_ACCOUNT"]
        )
        + datetime.timedelta(days=DELAY_FOR_FIRST_EMAIL)
    )
    long_inactive_date = test_date - datetime.timedelta(
        days=2 * client_app.app.config["INACTIVITY_TIMER_CLEANUP_ACCOUNT"]
    )

    # user's own activity is long expired, but their meeting was used recently
    user.last_connection_utc_datetime = long_inactive_date
    user.created_at = long_inactive_date
    meeting.last_connection_utc_datetime = first_mail_date
    meeting.created_at = first_mail_date

    # user_2 has the same expired activity but no meeting to keep it alive
    user_2.last_connection_utc_datetime = long_inactive_date
    user_2.created_at = long_inactive_date
    db.session.commit()

    time_machine.move_to(test_date)
    inform_user_before_account_deletion()
    users_to_inform = get_inactive_users_to_inform()

    assert users_to_inform == [(user, DELAY_FOR_FIRST_EMAIL)]
    assert len(smtpd.messages) == 1

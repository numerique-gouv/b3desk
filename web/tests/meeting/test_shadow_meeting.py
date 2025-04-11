import datetime

from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import delete_all_old_shadow_meetings
from b3desk.models.meetings import get_all_previous_voiceBridges
from b3desk.models.meetings import get_or_create_shadow_meeting
from b3desk.models.roles import Role


def test_delete_all_old_shadow_meetings(
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    shadow_meeting_2,
    shadow_meeting_3,
    user,
):
    delete_all_old_shadow_meetings()
    voiceBridges = get_all_previous_voiceBridges()
    assert voiceBridges == ["555555552", "555555553"]
    assert user.meetings == [meeting, meeting_2, meeting_3, shadow_meeting]
    assert get_or_create_shadow_meeting(user) == shadow_meeting


def test_get_or_create_shadow_meeting(user):
    assert get_or_create_shadow_meeting(user).name == "le séminaire de Alice Cooper"


def test_get_or_create_shadow_meeting_with_existing_shadow_meeting(
    user, shadow_meeting
):
    assert get_or_create_shadow_meeting(user) == shadow_meeting


def test_join_meeting_as_moderator_correctly_save_last_connection_date(
    client_app, shadow_meeting, user, bbb_response
):
    meeting_hash = shadow_meeting.get_hash(Role.moderator)
    previous_connection = shadow_meeting.last_connection_utc_datetime

    url = f"/meeting/signin/{shadow_meeting.id}/creator/{shadow_meeting.user.id}/hash/{meeting_hash}"
    response = client_app.get(
        url, extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=200
    )

    join_url = "/meeting/join"
    assert join_url == response.form.action

    response = response.form.submit()

    meeting = db.session.get(Meeting, 1)
    assert previous_connection != meeting.last_connection_utc_datetime
    assert (
        meeting.last_connection_utc_datetime.date() == datetime.datetime.today().date()
    )


def test_join_meeting_as_attendee_not_save_last_connection_date(
    client_app, shadow_meeting, authenticated_attendee, bbb_response
):
    meeting_hash = shadow_meeting.get_hash(Role.attendee)

    url = f"/meeting/signin/{shadow_meeting.id}/creator/{shadow_meeting.user.id}/hash/{meeting_hash}"
    response = client_app.get(
        url, extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=200
    )

    join_url = "/meeting/join"
    assert join_url == response.form.action

    response = response.form.submit()

    meeting = db.session.get(Meeting, 1)
    assert meeting.last_connection_utc_datetime == datetime.datetime(2025, 1, 1)

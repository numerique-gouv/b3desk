import datetime

from b3desk.join import get_hash
from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import create_and_save_hidden_meeting
from b3desk.models.meetings import delete_all_old_hidden_meetings
from b3desk.models.meetings import get_all_previous_voiceBridges
from b3desk.models.roles import Role


def test_delete_all_old_hidden_meetings(
    time_machine,
    meeting,
    meeting_2,
    meeting_3,
    hidden_meeting,
    hidden_meeting_2,
    hidden_meeting_3,
    user,
):
    """Test that old hidden meetings are deleted except the most recent one."""
    time_machine.move_to(datetime.datetime(2025, 6, 1))
    delete_all_old_hidden_meetings()
    voiceBridges = get_all_previous_voiceBridges()
    assert voiceBridges == ["555555552", "555555553"]
    assert user.meetings == [meeting, meeting_2, meeting_3, hidden_meeting]
    new_meeting = create_and_save_hidden_meeting(user)
    assert user.meetings == [meeting, meeting_2, meeting_3, hidden_meeting, new_meeting]


def test_create_and_save_hidden_meeting(client_app, user):
    """Test that hidden meeting is created with default configuration."""
    assert create_and_save_hidden_meeting(user).name == "le séminaire de Alice Cooper"
    assert (
        create_and_save_hidden_meeting(user).welcome
        == f"Bienvenue dans le séminaire de {user.fullname}"
    )
    assert create_and_save_hidden_meeting(user).duration == 280
    assert create_and_save_hidden_meeting(user).maxParticipants == 350
    assert (
        create_and_save_hidden_meeting(user).logoutUrl
        == client_app.app.config["MEETING_LOGOUT_URL"]
    )
    assert (
        create_and_save_hidden_meeting(user).moderatorOnlyMessage
        == "Bienvenue aux modérateurs"
    )
    assert not create_and_save_hidden_meeting(user).record
    assert not create_and_save_hidden_meeting(user).autoStartRecording
    assert not create_and_save_hidden_meeting(user).allowStartStopRecording
    assert not create_and_save_hidden_meeting(user).lockSettingsDisableMic
    assert not create_and_save_hidden_meeting(user).lockSettingsDisablePrivateChat
    assert not create_and_save_hidden_meeting(user).lockSettingsDisablePublicChat
    assert not create_and_save_hidden_meeting(user).lockSettingsDisableNote
    assert not create_and_save_hidden_meeting(user).lockSettingsDisableCam
    assert not create_and_save_hidden_meeting(user).allowModsToUnmuteUsers
    assert not create_and_save_hidden_meeting(user).webcamsOnlyForModerator
    assert create_and_save_hidden_meeting(user).muteOnStart
    assert not create_and_save_hidden_meeting(user).guestPolicy
    assert not create_and_save_hidden_meeting(user).logo
    assert create_and_save_hidden_meeting(user).is_hidden
    assert create_and_save_hidden_meeting(user).owner == user
    assert create_and_save_hidden_meeting(user).attendeePW
    assert create_and_save_hidden_meeting(user).moderatorPW
    assert create_and_save_hidden_meeting(user).voiceBridge.isdigit()
    assert create_and_save_hidden_meeting(user).visio_code.isdigit()


def test_create_and_save_hidden_meeting_with_existing_hidden_meeting(
    user, hidden_meeting
):
    """Test that existing hidden meeting is returned instead of creating new one."""
    assert create_and_save_hidden_meeting(user) != hidden_meeting


CREATE_RESPONSE = """
<response>
  <returncode>SUCCESS</returncode>
  <meetingID>Test</meetingID>
  <voiceBridge>70757</voiceBridge>
  <running>false</running>
</response>
"""


def test_join_meeting_as_moderator_correctly_save_last_connection_date(
    client_app, hidden_meeting, user, mocker
):
    """Test that last connection date is updated when moderator joins meeting."""

    class ResponseBBBcreate:
        content = CREATE_RESPONSE
        text = ""

    meeting_hash = get_hash(hidden_meeting, Role.moderator)
    previous_connection = hidden_meeting.last_connection_utc_datetime

    url = f"/meeting/signin/{hidden_meeting.id}/hash/{meeting_hash}"
    response = client_app.get(
        url, extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=200
    )

    join_url = "/meeting/join"
    assert join_url == response.form.action
    mocker.patch("requests.Session.send", return_value=ResponseBBBcreate)

    response.form.submit()

    meeting = db.session.get(Meeting, 1)
    assert previous_connection != meeting.last_connection_utc_datetime
    assert (
        meeting.last_connection_utc_datetime.date() == datetime.datetime.today().date()
    )


def test_join_meeting_as_attendee_not_save_last_connection_date(
    client_app, hidden_meeting, authenticated_attendee, mocker
):
    """Test that last connection date is not updated when attendee joins meeting."""

    class ResponseBBBcreate:
        content = CREATE_RESPONSE
        text = ""

    meeting_hash = get_hash(hidden_meeting, Role.attendee)

    url = f"/meeting/signin/{hidden_meeting.id}/hash/{meeting_hash}"
    response = client_app.get(
        url, extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=200
    )

    join_url = "/meeting/join"
    assert join_url == response.form.action

    mocker.patch("requests.Session.send", return_value=ResponseBBBcreate)

    response = response.form.submit()

    meeting = db.session.get(Meeting, 1)
    assert meeting.last_connection_utc_datetime == datetime.datetime(2025, 1, 1)

import datetime

from b3desk.join import get_hash
from b3desk.models import db
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import delete_all_old_shadow_meetings
from b3desk.models.meetings import get_all_previous_voiceBridges
from b3desk.models.meetings import get_or_create_shadow_meeting
from b3desk.models.roles import Role


def test_delete_all_old_shadow_meetings(
    time_machine,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    shadow_meeting_2,
    shadow_meeting_3,
    user,
):
    """Test that old shadow meetings are deleted except the most recent one."""
    time_machine.move_to(datetime.datetime(2025, 6, 1))
    delete_all_old_shadow_meetings()
    voiceBridges = get_all_previous_voiceBridges()
    assert voiceBridges == ["555555552", "555555553"]
    assert user.meetings == [meeting, meeting_2, meeting_3, shadow_meeting]
    assert get_or_create_shadow_meeting(user) == shadow_meeting


def test_get_or_create_shadow_meeting(client_app, user):
    """Test that shadow meeting is created with default configuration."""
    assert get_or_create_shadow_meeting(user).name == "le séminaire de Alice Cooper"
    assert (
        get_or_create_shadow_meeting(user).welcome
        == f"Bienvenue dans {client_app.app.config['WORDING_THE_MEETING']} de {user.fullname}"
    )
    assert get_or_create_shadow_meeting(user).duration == 280
    assert get_or_create_shadow_meeting(user).maxParticipants == 350
    assert (
        get_or_create_shadow_meeting(user).logoutUrl
        == client_app.app.config["MEETING_LOGOUT_URL"]
    )
    assert (
        get_or_create_shadow_meeting(user).moderatorOnlyMessage
        == "Bienvenue aux modérateurs"
    )
    assert not get_or_create_shadow_meeting(user).record
    assert not get_or_create_shadow_meeting(user).autoStartRecording
    assert not get_or_create_shadow_meeting(user).allowStartStopRecording
    assert not get_or_create_shadow_meeting(user).lockSettingsDisableMic
    assert not get_or_create_shadow_meeting(user).lockSettingsDisablePrivateChat
    assert not get_or_create_shadow_meeting(user).lockSettingsDisablePublicChat
    assert not get_or_create_shadow_meeting(user).lockSettingsDisableNote
    assert not get_or_create_shadow_meeting(user).lockSettingsDisableCam
    assert not get_or_create_shadow_meeting(user).allowModsToUnmuteUsers
    assert not get_or_create_shadow_meeting(user).webcamsOnlyForModerator
    assert get_or_create_shadow_meeting(user).muteOnStart
    assert not get_or_create_shadow_meeting(user).guestPolicy
    assert not get_or_create_shadow_meeting(user).logo
    assert get_or_create_shadow_meeting(user).is_shadow
    assert get_or_create_shadow_meeting(user).user == user
    assert get_or_create_shadow_meeting(user).attendeePW
    assert get_or_create_shadow_meeting(user).moderatorPW
    assert get_or_create_shadow_meeting(user).voiceBridge.isdigit()
    assert get_or_create_shadow_meeting(user).visio_code.isdigit()


def test_get_or_create_shadow_meeting_with_existing_shadow_meeting(
    user, shadow_meeting
):
    """Test that existing shadow meeting is returned instead of creating new one."""
    assert get_or_create_shadow_meeting(user) == shadow_meeting


CREATE_RESPONSE = """
<response>
  <returncode>SUCCESS</returncode>
  <meetingID>Test</meetingID>
  <voiceBridge>70757</voiceBridge>
  <running>false</running>
</response>
"""


def test_join_meeting_as_moderator_correctly_save_last_connection_date(
    client_app, shadow_meeting, user, mocker
):
    """Test that last connection date is updated when moderator joins meeting."""

    class ResponseBBBcreate:
        content = CREATE_RESPONSE
        text = ""

    meeting_hash = get_hash(shadow_meeting, Role.moderator)
    previous_connection = shadow_meeting.last_connection_utc_datetime

    url = f"/meeting/signin/{shadow_meeting.id}/hash/{meeting_hash}"
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
    client_app, shadow_meeting, authenticated_attendee, mocker
):
    """Test that last connection date is not updated when attendee joins meeting."""

    class ResponseBBBcreate:
        content = CREATE_RESPONSE
        text = ""

    meeting_hash = get_hash(shadow_meeting, Role.attendee)

    url = f"/meeting/signin/{shadow_meeting.id}/hash/{meeting_hash}"
    response = client_app.get(
        url, extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=200
    )

    join_url = "/meeting/join"
    assert join_url == response.form.action

    mocker.patch("requests.Session.send", return_value=ResponseBBBcreate)

    response = response.form.submit()

    meeting = db.session.get(Meeting, 1)
    assert meeting.last_connection_utc_datetime == datetime.datetime(2025, 1, 1)

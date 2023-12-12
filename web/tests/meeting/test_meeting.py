from unittest import mock

import pytest
from flaskr.models import Meeting
from flaskr.models import MODERATOR_ONLY_MESSAGE_MAXLENGTH


@pytest.fixture()
def mocked_is_meeting_running(mocker):
    mocker.patch("flaskr.models.Meeting.is_meeting_running", return_value=False)


def test_show_meeting(client_app, app, authenticated_user, meeting, bbb_response):
    response = client_app.get(f"/meeting/show/{meeting.id}", status=200)

    assert "meeting/show.html" in response.contexts


def test_show_meeting_recording(
    client_app, app, authenticated_user, meeting, bbb_response
):
    response = client_app.get(f"/meeting/recordings/{meeting.id}", status=200)

    assert "meeting/recordings.html" in response.contexts


def test_new_meeting(client_app, authenticated_user):
    response = client_app.get("/meeting/new", status=200)

    assert response.template == "meeting/wizard.html"


def test_new_meeting_when_recording_not_configured(client_app, app, authenticated_user):
    app.config["RECORDING"] = False

    response = client_app.get("/meeting/new")

    response.mustcontain(no="Enregistrement")


def test_edit_meeting(client_app, app, authenticated_user, meeting, bbb_response):
    response = client_app.get(f"/meeting/edit/{meeting.id}", status=200)

    assert response.template == "meeting/wizard.html"


MEETING_DATA = {
    "name": "Mon meeting de test",
    "welcome": "Bienvenue dans mon meeting de test",
    "maxParticipants": 5,
    "duration": 60,
    "guestPolicy": "on",
    "webcamsOnlyForModerator": "on",
    "muteOnStart": "on",
    "lockSettingsDisableCam": "on",
    "lockSettingsDisableMic": "on",
    "lockSettingsDisablePrivateChat": "on",
    "lockSettingsDisablePublicChat": "on",
    "lockSettingsDisableNote": "on",
    "moderatorOnlyMessage": "Bienvenue aux modérateurs",
    "logoutUrl": "https://log.out",
    "moderatorPW": "Motdepasse1",
    "attendeePW": "Motdepasse2",
    "autoStartRecording": "on",
    "allowStartStopRecording": "on",
}


def test_save_new_meeting(
    app, client_app, authenticated_user, mocked_is_meeting_running
):
    response = client_app.post(
        "/meeting/save",
        MEETING_DATA,
        status=302,
    )

    assert "welcome" in response.location

    meeting = Meeting.query.get(1)

    assert meeting.user_id == 1
    assert meeting.name == "Mon meeting de test"
    assert meeting.welcome == "Bienvenue dans mon meeting de test"
    assert meeting.maxParticipants == 5
    assert meeting.duration == 60
    assert meeting.guestPolicy is True
    assert meeting.webcamsOnlyForModerator is True
    assert meeting.muteOnStart is True
    assert meeting.lockSettingsDisableCam is True
    assert meeting.lockSettingsDisableMic is True
    assert meeting.lockSettingsDisablePrivateChat is True
    assert meeting.lockSettingsDisablePublicChat is True
    assert meeting.lockSettingsDisableNote is True
    assert meeting.moderatorOnlyMessage == "Bienvenue aux modérateurs"
    assert meeting.logoutUrl == "https://log.out"
    assert meeting.moderatorPW == "Motdepasse1"
    assert meeting.attendeePW == "Motdepasse2"
    assert meeting.record is True
    assert meeting.autoStartRecording is True
    assert meeting.allowStartStopRecording is True


def test_save_existing_meeting(
    app, client_app, authenticated_user, meeting, mocked_is_meeting_running
):
    assert len(Meeting.query.all()) == 1

    data = MEETING_DATA.copy()
    data["id"] = meeting.id

    response = client_app.post(
        "/meeting/save",
        data,
        status=302,
    )

    assert "welcome" in response.location

    assert len(Meeting.query.all()) == 1

    meeting = Meeting.query.get(1)

    assert meeting.user_id == 1
    assert not meeting.name  # Name can not be edited
    assert meeting.welcome == "Bienvenue dans mon meeting de test"
    assert meeting.maxParticipants == 5
    assert meeting.duration == 60
    assert meeting.guestPolicy is True
    assert meeting.webcamsOnlyForModerator is True
    assert meeting.muteOnStart is True
    assert meeting.lockSettingsDisableCam is True
    assert meeting.lockSettingsDisableMic is True
    assert meeting.lockSettingsDisablePrivateChat is True
    assert meeting.lockSettingsDisablePublicChat is True
    assert meeting.lockSettingsDisableNote is True
    assert meeting.moderatorOnlyMessage == "Bienvenue aux modérateurs"
    assert meeting.logoutUrl == "https://log.out"
    assert meeting.moderatorPW == "Motdepasse1"
    assert meeting.attendeePW == "Motdepasse2"
    assert meeting.record is True
    assert meeting.autoStartRecording is True
    assert meeting.allowStartStopRecording is True


def test_save_moderatorOnlyMessage_too_long(
    app, client_app, authenticated_user, mocked_is_meeting_running
):
    data = MEETING_DATA.copy()
    moderator_only_message = "a" * (MODERATOR_ONLY_MESSAGE_MAXLENGTH + 1)
    data["moderatorOnlyMessage"] = moderator_only_message

    response = client_app.post(
        "/meeting/save",
        data,
        status=200,
    )
    assert response.template == "meeting/wizard.html"

    response.mustcontain("Le formulaire contient des erreurs")
    response.mustcontain(moderator_only_message)
    response.mustcontain("Le message est trop long")
    assert not Meeting.query.all()


def test_save_no_recording_by_default(
    app, client_app, authenticated_user, mocked_is_meeting_running
):
    data = MEETING_DATA.copy()
    del data["autoStartRecording"]
    del data["allowStartStopRecording"]

    client_app.post("/meeting/save", data, status=302)

    meeting = Meeting.query.get(1)
    assert meeting.record is False
    assert meeting.autoStartRecording is False
    assert meeting.allowStartStopRecording is False


def test_save_meeting_in_no_recording_environment(
    app, client_app, authenticated_user, mocked_is_meeting_running
):
    app.config["RECORDING"] = False

    response = client_app.post(
        "/meeting/save",
        MEETING_DATA,
        status=302,
    )

    assert "welcome" in response.location

    assert len(Meeting.query.all()) == 1
    meeting = Meeting.query.get(1)
    assert meeting.record is False


def test_create(app, meeting, mocker):
    app.config["FILE_SHARING"] = True

    class Resp:
        content = """<response><returncode>SUCCESS</returncode></response>"""

    mocked_bbb_create_request = mocker.patch("requests.post", return_value=Resp)
    mocked_background_upload = mocker.patch(
        "flaskr.tasks.background_upload.delay", return_value=True
    )

    with app.test_request_context():
        meeting.name = "My Meeting"
        meeting.attendeePW = "Password1"
        meeting.moderatorPW = "Password2"
        meeting.welcome = "Welcome!"
        meeting.maxParticipants = 25
        meeting.logoutUrl = "https://log.out"
        meeting.record = True
        meeting.duration = 60
        meeting.moderatorOnlyMessage = "Welcome moderators!"
        meeting.autoStartRecording = False
        meeting.allowStartStopRecording = True
        meeting.webcamsOnlyForModerator = False
        meeting.muteOnStart = True
        meeting.lockSettingsDisableCam = False
        meeting.lockSettingsDisableMic = False
        meeting.allowModsToUnmuteUsers = False
        meeting.lockSettingsDisablePrivateChat = False
        meeting.lockSettingsDisablePublicChat = False
        meeting.lockSettingsDisableNote = False
        meeting.guestPolicy = True

        meeting.bbb.create()

    assert mocked_bbb_create_request.called
    bbb_url = mocked_bbb_create_request.call_args.args[0]
    assert bbb_url == f'{app.config["BIGBLUEBUTTON_ENDPOINT"]}/create'
    bbb_params = mocked_bbb_create_request.call_args.kwargs["params"]
    assert bbb_params == {
        "meetingID": meeting.meetingID,
        "name": "My Meeting",
        "meetingKeepEvents": "true",
        "meta_analytics-callback-url": "https://bbb-analytics-staging.osc-fr1.scalingo.io/v1/post_events",
        "attendeePW": "Password1",
        "moderatorPW": "Password2",
        "welcome": "Welcome!",
        "maxParticipants": "25",
        "logoutURL": "https://log.out",
        "record": "true",
        "duration": "60",
        "moderatorOnlyMessage": "Welcome moderators!\n\n Lien Modérateur   :\n\nhttp://localhost:5000/meeting/signin/1/creator/1/hash/74416cd20fdc0ce5f59ff198915c82515e1e375f\n\n Lien Participant   :\n\nhttp://localhost:5000/meeting/signin/1/creator/1/hash/b3f8a558fb7cfc889405fd1b8c1c8d933db00334",
        "autoStartRecording": "false",
        "allowStartStopRecording": "true",
        "webcamsOnlyForModerator": "false",
        "muteOnStart": "true",
        "lockSettingsDisableCam": "false",
        "lockSettingsDisableMic": "false",
        "allowModsToUnmuteUsers": "false",
        "lockSettingsDisablePrivateChat": "false",
        "lockSettingsDisablePublicChat": "false",
        "lockSettingsDisableNote": "false",
        "guestPolicy": "ASK_MODERATOR",
        "checksum": mock.ANY,
        "uploadExternalDescription": app.config["EXTERNAL_UPLOAD_DESCRIPTION"],
        "uploadExternalUrl": f"{app.config['SERVER_FQDN']}/meeting/{str(meeting.id)}/externalUpload",
    }

    assert mocked_background_upload.called
    assert (
        mocked_background_upload.call_args.args[0]
        == f'{app.config["BIGBLUEBUTTON_ENDPOINT"]}/insertDocument'
    )
    assert (
        mocked_background_upload.call_args.args[1]
        == "<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'>  </module></modules>"
    )
    assert mocked_background_upload.call_args.args[2] == {
        "meetingID": meeting.meetingID,
        "checksum": mock.ANY,
    }


def test_create_without_logout_url_gets_default(
    app, client_app, authenticated_user, mocked_is_meeting_running
):
    data = MEETING_DATA.copy()
    del data["logoutUrl"]

    client_app.post(
        "/meeting/save",
        data,
        status=302,
    )

    meeting = Meeting.query.get(1)
    assert meeting
    assert meeting.logoutUrl == app.config["MEETING_LOGOUT_URL"]


def test_create_quick_meeting(app, monkeypatch, user, mocker):
    from flaskr.routes import get_quick_meeting_from_user_and_random_string

    class Resp:
        content = """<response><returncode>SUCCESS</returncode></response>"""

    mocked_bbb_create_request = mocker.patch("requests.post", return_value=Resp)
    mocker.patch("flaskr.tasks.background_upload.delay", return_value=True)
    with app.test_request_context():
        monkeypatch.setattr("flaskr.models.User.id", 1)
        monkeypatch.setattr("flaskr.models.User.hash", "hash")
        meeting = get_quick_meeting_from_user_and_random_string(user)
        meeting.bbb.create()

    assert mocked_bbb_create_request.called
    bbb_url = mocked_bbb_create_request.call_args.args[0]
    assert bbb_url == f'{app.config["BIGBLUEBUTTON_ENDPOINT"]}/create'
    bbb_params = mocked_bbb_create_request.call_args.kwargs["params"]
    assert bbb_params == {
        "meetingID": meeting.meetingID,
        "name": "Séminaire improvisé",
        "uploadExternalUrl": "http://localhost:5000/meeting/None/externalUpload",
        "uploadExternalDescription": "Fichiers depuis votre Nextcloud",
        "attendeePW": meeting.attendeePW,
        "moderatorPW": meeting.moderatorPW,
        "logoutURL": "http://education.gouv.fr/",
        "duration": "280",
        "meetingKeepEvents": "true",
        "meta_analytics-callback-url": "https://bbb-analytics-staging.osc-fr1.scalingo.io/v1/post_events",
        "moderatorOnlyMessage": f"Bienvenue aux modérateurs. Pour inviter quelqu'un à ce séminaire, envoyez-lui l'un de ces liens :\n\n Lien Modérateur   :\n\nhttp://localhost:5000/meeting/signin/{meeting.fake_id}/creator/1/hash/{meeting.get_hash('moderator')}\n\n Lien Participant   :\n\nhttp://localhost:5000/meeting/signin/{meeting.fake_id}/creator/1/hash/{meeting.get_hash('attendee')}",
        "guestPolicy": "ALWAYS_ACCEPT",
        "checksum": mock.ANY,
    }


def test_edit_files_meeting(client_app, app, authenticated_user, meeting, bbb_response):
    app.config["FILE_SHARING"] = True

    response = client_app.get(f"/meeting/files/{meeting.id}", status=200)

    assert response.template == "meeting/filesform.html"


def test_deactivated_meeting_files_cannot_access_files(
    client_app, app, authenticated_user, meeting, bbb_response
):
    app.config["FILE_SHARING"] = False

    response = client_app.get("/welcome", status=200)

    response.mustcontain(no="Fichiers associés à ")


def test_deactivated_meeting_files_cannot_edit(
    client_app, app, authenticated_user, meeting, bbb_response
):
    app.config["FILE_SHARING"] = False

    response = client_app.get(f"/meeting/files/{meeting.id}", status=302)

    assert "welcome" in response.location

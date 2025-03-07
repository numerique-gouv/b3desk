import datetime
import hashlib
import os
from unittest import mock
from urllib.parse import parse_qs
from urllib.parse import urlparse

import pytest

from b3desk.models import db
from b3desk.models.meetings import MODERATOR_ONLY_MESSAGE_MAXLENGTH
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingFiles
from b3desk.models.roles import Role


@pytest.fixture()
def mock_meeting_is_running(mocker):
    mocker.patch("b3desk.models.meetings.Meeting.is_running", return_value=True)


@pytest.fixture()
def mock_meeting_is_not_running(mocker):
    mocker.patch("b3desk.models.meetings.Meeting.is_running", return_value=False)


def test_show_meeting(client_app, authenticated_user, meeting, bbb_response):
    response = client_app.get(f"/meeting/show/{meeting.id}", status=200)

    assert "meeting/show.html" in response.contexts


def test_show_meeting_recording(client_app, authenticated_user, meeting, bbb_response):
    response = client_app.get(f"/meeting/recordings/{meeting.id}", status=200)

    assert "meeting/recordings.html" in response.contexts


def test_new_meeting(client_app, authenticated_user):
    response = client_app.get("/meeting/new", status=200)

    assert response.template == "meeting/wizard.html"


def test_new_meeting_when_recording_not_configured(client_app, authenticated_user):
    client_app.app.config["RECORDING"] = False

    response = client_app.get("/meeting/new")

    response.mustcontain(no="Enregistrement")


def test_edit_meeting(client_app, authenticated_user, meeting, bbb_response):
    response = client_app.get(f"/meeting/edit/{meeting.id}", status=200)

    assert response.template == "meeting/wizard.html"


def test_save_new_meeting(client_app, authenticated_user, mock_meeting_is_not_running):
    res = client_app.get("/meeting/new")
    res.form["name"] = "Mon meeting de test"
    res.form["welcome"] = "Bienvenue dans mon meeting de test"
    res.form["maxParticipants"] = 5
    res.form["duration"] = 60
    res.form["guestPolicy"] = "on"
    res.form["webcamsOnlyForModerator"] = "on"
    res.form["muteOnStart"] = "on"
    res.form["lockSettingsDisableCam"] = "on"
    res.form["lockSettingsDisableMic"] = "on"
    res.form["lockSettingsDisablePrivateChat"] = "on"
    res.form["lockSettingsDisablePublicChat"] = "on"
    res.form["lockSettingsDisableNote"] = "on"
    res.form["moderatorOnlyMessage"] = "Bienvenue aux modérateurs"
    res.form["logoutUrl"] = "https://log.out"
    res.form["moderatorPW"] = "Motdepasse1"
    res.form["attendeePW"] = "Motdepasse2"
    res.form["autoStartRecording"] = "on"
    res.form["allowStartStopRecording"] = "on"

    res = res.form.submit()
    assert (
        "success",
        "Mon meeting de test modifications prises en compte",
    ) in res.flashes

    meeting = db.session.get(Meeting, 1)

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


def test_save_existing_meeting_not_running(
    client_app, authenticated_user, meeting, mock_meeting_is_not_running
):
    assert len(Meeting.query.all()) == 1

    res = client_app.get("/meeting/edit/1")
    res.form["name"] = "Mon meeting de test"
    res.form["welcome"] = "Bienvenue dans mon meeting de test"
    res.form["maxParticipants"] = 5
    res.form["duration"] = 60
    res.form["guestPolicy"] = "on"
    res.form["webcamsOnlyForModerator"] = "on"
    res.form["muteOnStart"] = "on"
    res.form["lockSettingsDisableCam"] = "on"
    res.form["lockSettingsDisableMic"] = "on"
    res.form["lockSettingsDisablePrivateChat"] = "on"
    res.form["lockSettingsDisablePublicChat"] = "on"
    res.form["lockSettingsDisableNote"] = "on"
    res.form["moderatorOnlyMessage"] = "Bienvenue aux modérateurs"
    res.form["logoutUrl"] = "https://log.out"
    res.form["moderatorPW"] = "Motdepasse1"
    res.form["attendeePW"] = "Motdepasse2"
    res.form["autoStartRecording"] = "on"
    res.form["allowStartStopRecording"] = "on"

    res = res.form.submit()
    assert ("success", "meeting modifications prises en compte") in res.flashes

    assert len(Meeting.query.all()) == 1
    meeting = db.session.get(Meeting, 1)

    assert meeting.user_id == 1
    assert meeting.name == "meeting"  # Name can not be edited
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


def test_save_existing_meeting_running(
    mocker, client_app, authenticated_user, meeting, mock_meeting_is_running
):
    mocker.patch("b3desk.models.meetings.Meeting.end_bbb", return_value=True)
    assert len(Meeting.query.all()) == 1

    res = client_app.get("/meeting/edit/1")
    res.form["welcome"] = "Bienvenue dans mon meeting de test"

    res = res.form.submit()
    assert res.template == "meeting/end.html"
    assert ("success", "meeting modifications prises en compte") in res.flashes

    assert len(Meeting.query.all()) == 1
    meeting = db.session.get(Meeting, 1)
    assert meeting.welcome == "Bienvenue dans mon meeting de test"

    res = res.form.submit()
    assert ("success", "Séminaire « meeting » terminé(e)") in res.flashes


def test_save_moderatorOnlyMessage_too_long(
    client_app, authenticated_user, mock_meeting_is_not_running
):
    res = client_app.get("/meeting/new")
    moderator_only_message = "a" * (MODERATOR_ONLY_MESSAGE_MAXLENGTH + 1)
    res.form["moderatorOnlyMessage"] = moderator_only_message
    res = res.form.submit()

    res.mustcontain("Le formulaire contient des erreurs")
    res.mustcontain(moderator_only_message)
    res.mustcontain("Le message est trop long")
    assert not Meeting.query.all()


def test_save_no_recording_by_default(
    client_app, authenticated_user, mock_meeting_is_not_running
):
    res = client_app.get("/meeting/new")
    res.form["name"] = "Mon meeting de test"
    res.form["maxParticipants"] = 5
    res.form["duration"] = 60
    res.form["moderatorPW"] = "Motdepasse1"
    res.form["attendeePW"] = "Motdepasse2"

    res = res.form.submit()
    assert (
        "success",
        "Mon meeting de test modifications prises en compte",
    ) in res.flashes

    meeting = db.session.get(Meeting, 1)
    assert meeting.record is False
    assert meeting.autoStartRecording is False
    assert meeting.allowStartStopRecording is False


def test_save_meeting_in_no_recording_environment(
    client_app, authenticated_user, mock_meeting_is_not_running
):
    assert len(Meeting.query.all()) == 0
    client_app.app.config["RECORDING"] = False

    res = client_app.get("/meeting/new")
    res.form["name"] = "Mon meeting de test"
    res.form["maxParticipants"] = 5
    res.form["duration"] = 60
    res.form["moderatorPW"] = "Motdepasse1"
    res.form["attendeePW"] = "Motdepasse2"

    assert "allowStartStopRecording" not in res.form.fields
    assert "autoStartRecording" not in res.form.fields

    res = res.form.submit()
    assert (
        "success",
        "Mon meeting de test modifications prises en compte",
    ) in res.flashes

    assert len(Meeting.query.all()) == 1
    meeting = db.session.get(Meeting, 1)
    assert meeting.record is False


def test_create_no_file(client_app, meeting, mocker, bbb_response):
    """Tests the BBB meeting creation request.

    As there is no file attached to the meeting, no background upload
    task should be called.
    """
    client_app.app.config["FILE_SHARING"] = True

    mocked_background_upload = mocker.patch(
        "b3desk.tasks.background_upload.delay", return_value=True
    )

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

    assert bbb_response.called
    bbb_url = bbb_response.call_args.args[0].url
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/create"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }
    assert bbb_params == {
        "meetingID": meeting.meetingID,
        "name": "My Meeting",
        "meetingKeepEvents": "true",
        "meta_analytics-callback-url": "https://bbb-analytics-staging.osc-fr1.scalingo.io/v1/post_events",
        "meta_academy": "domain.tld",
        "attendeePW": "Password1",
        "moderatorPW": "Password2",
        "welcome": "Welcome!",
        "maxParticipants": "25",
        "logoutURL": "https://log.out",
        "record": "true",
        "duration": "60",
        "moderatorOnlyMessage": f'Welcome moderators!<br />\n\n Lien Modérateur   : <a href="http://localhost:5000/meeting/signin/moderateur/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.moderator)}" target="_blank">http://localhost:5000/meeting/signin/moderateur/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.moderator)}</a><br />\n\n Lien Participant   : <a href="http://localhost:5000/meeting/signin/invite/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.attendee)}" target="_blank">http://localhost:5000/meeting/signin/invite/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.attendee)}</a>',
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
        "uploadExternalDescription": client_app.app.config[
            "EXTERNAL_UPLOAD_DESCRIPTION"
        ],
        "uploadExternalUrl": f"http://localhost:5000/meeting/{str(meeting.id)}/externalUpload",
    }

    assert not mocked_background_upload.called


def test_create_with_only_a_default_file(
    client_app, meeting, mocker, bbb_response, jpg_file_content, tmp_path
):
    """Tests the BBB meeting creation request.

    A default file, which is no longer a real functionnality, attached
    to the meeting, should always be sent asynchronously, background
    upload task should be called.
    """
    client_app.app.config["FILE_SHARING"] = True

    file_path = os.path.join(tmp_path, "foobar.jpg")
    with open(file_path, "wb") as fd:
        fd.write(jpg_file_content)

    mocked_background_upload = mocker.patch(
        "b3desk.tasks.background_upload.delay", return_value=True
    )

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

    meeting_file = MeetingFiles(
        nc_path=file_path,
        title="file_title",
        created_at=datetime.date(2024, 3, 19),
        meeting_id=meeting.id,
        is_default=True,
    )
    meeting.files = [meeting_file]

    meeting.bbb.create()

    assert bbb_response.called
    bbb_url = bbb_response.call_args.args[0].url
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/create"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }
    assert bbb_params == {
        "meetingID": meeting.meetingID,
        "name": "My Meeting",
        "meetingKeepEvents": "true",
        "meta_analytics-callback-url": "https://bbb-analytics-staging.osc-fr1.scalingo.io/v1/post_events",
        "meta_academy": "domain.tld",
        "attendeePW": "Password1",
        "moderatorPW": "Password2",
        "welcome": "Welcome!",
        "maxParticipants": "25",
        "logoutURL": "https://log.out",
        "record": "true",
        "duration": "60",
        "moderatorOnlyMessage": f'Welcome moderators!<br />\n\n Lien Modérateur   : <a href="http://localhost:5000/meeting/signin/moderateur/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.moderator)}" target="_blank">http://localhost:5000/meeting/signin/moderateur/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.moderator)}</a><br />\n\n Lien Participant   : <a href="http://localhost:5000/meeting/signin/invite/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.attendee)}" target="_blank">http://localhost:5000/meeting/signin/invite/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.attendee)}</a>',
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
        "uploadExternalDescription": client_app.app.config[
            "EXTERNAL_UPLOAD_DESCRIPTION"
        ],
        "uploadExternalUrl": f"http://localhost:5000/meeting/{str(meeting.id)}/externalUpload",
    }

    assert mocked_background_upload.called


def test_create_with_files(
    client_app, meeting, mocker, bbb_response, jpg_file_content, tmp_path
):
    """Tests the BBB meeting creation request.

    As there is a non default file attached to the meeting, the
    background upload task should be called.
    """
    client_app.app.config["FILE_SHARING"] = True

    file_path = os.path.join(tmp_path, "foobar.jpg")
    with open(file_path, "wb") as fd:
        fd.write(jpg_file_content)

    mocked_background_upload = mocker.patch(
        "b3desk.tasks.background_upload.delay", return_value=True
    )

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

    meeting_file = MeetingFiles(
        nc_path=file_path,
        title="file_title",
        created_at=datetime.date(2024, 3, 19),
        meeting_id=meeting.id,
        is_default=False,
    )
    meeting.files = [meeting_file]

    meeting.bbb.create()

    assert bbb_response.called
    bbb_url = bbb_response.call_args.args[0].url
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/create"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }
    assert bbb_params == {
        "meetingID": meeting.meetingID,
        "name": "My Meeting",
        "meetingKeepEvents": "true",
        "meta_analytics-callback-url": "https://bbb-analytics-staging.osc-fr1.scalingo.io/v1/post_events",
        "meta_academy": "domain.tld",
        "attendeePW": "Password1",
        "moderatorPW": "Password2",
        "welcome": "Welcome!",
        "maxParticipants": "25",
        "logoutURL": "https://log.out",
        "record": "true",
        "duration": "60",
        "moderatorOnlyMessage": f'Welcome moderators!<br />\n\n Lien Modérateur   : <a href="http://localhost:5000/meeting/signin/moderateur/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.moderator)}" target="_blank">http://localhost:5000/meeting/signin/moderateur/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.moderator)}</a><br />\n\n Lien Participant   : <a href="http://localhost:5000/meeting/signin/invite/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.attendee)}" target="_blank">http://localhost:5000/meeting/signin/invite/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.attendee)}</a>',
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
        "uploadExternalDescription": client_app.app.config[
            "EXTERNAL_UPLOAD_DESCRIPTION"
        ],
        "uploadExternalUrl": f"http://localhost:5000/meeting/{str(meeting.id)}/externalUpload",
    }

    assert mocked_background_upload.called
    assert mocked_background_upload.call_args.args[0].startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/insertDocument"
    )

    secret_key = client_app.app.config["SECRET_KEY"]
    filehash = hashlib.sha1(
        f"{secret_key}-0-{meeting_file.id}-{secret_key}".encode()
    ).hexdigest()

    assert (
        mocked_background_upload.call_args.args[1]
        == "<?xml version='1.0' encoding='UTF-8'?> "
        + "<modules>  "
        + "<module name='presentation'> "
        + f"<document downloadable='false' url='http://localhost:5000/ncdownload/0/1/{filehash}/file_title' filename='file_title' /> "
        + "</module>"
        + "</modules>"
    )


def test_create_without_logout_url_gets_default(
    app, client_app, authenticated_user, mock_meeting_is_not_running
):
    res = client_app.get("/meeting/new")
    res = res.form.submit()
    assert ("success", "Mon Séminaire modifications prises en compte") in res.flashes

    meeting = db.session.get(Meeting, 1)
    assert meeting
    assert meeting.logoutUrl == app.config["MEETING_LOGOUT_URL"]


def test_create_quick_meeting(client_app, monkeypatch, user, mocker, bbb_response):
    from b3desk.endpoints.meetings import get_quick_meeting_from_user_and_random_string

    mocker.patch("b3desk.tasks.background_upload.delay", return_value=True)
    monkeypatch.setattr("b3desk.models.users.User.id", 1)
    monkeypatch.setattr("b3desk.models.users.User.hash", "hash")
    meeting = get_quick_meeting_from_user_and_random_string(user)
    meeting.bbb.create()

    assert bbb_response.called
    bbb_url = bbb_response.call_args.args[0].url
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/create"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }
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
        "meta_academy": "domain.tld",
        "moderatorOnlyMessage": f'Bienvenue aux modérateurs. Pour inviter quelqu\'un à ce séminaire, envoyez-lui l\'un de ces liens :<br />\n\n Lien Modérateur   : <a href="http://localhost:5000/meeting/signin/moderateur/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.moderator)}" target="_blank">http://localhost:5000/meeting/signin/moderateur/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.moderator)}</a><br />\n\n Lien Participant   : <a href="http://localhost:5000/meeting/signin/invite/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.attendee)}" target="_blank">http://localhost:5000/meeting/signin/invite/{meeting.fake_id}/creator/1/hash/{meeting.get_hash(Role.attendee)}</a>',
        "guestPolicy": "ALWAYS_ACCEPT",
        "checksum": mock.ANY,
    }


def test_edit_files_meeting(client_app, authenticated_user, meeting, bbb_response):
    client_app.app.config["FILE_SHARING"] = True

    response = client_app.get(f"/meeting/files/{meeting.id}", status=200)

    assert response.template == "meeting/filesform.html"


def test_deactivated_meeting_files_cannot_access_files(
    client_app, authenticated_user, meeting, bbb_response
):
    client_app.app.config["FILE_SHARING"] = False

    response = client_app.get("/welcome", status=200)

    response.mustcontain(no="Fichiers associés à ")


def test_deactivated_meeting_files_cannot_edit(
    client_app, authenticated_user, meeting, bbb_response
):
    client_app.app.config["FILE_SHARING"] = False

    response = client_app.get(f"/meeting/files/{meeting.id}", status=302)

    assert "welcome" in response.location


def test_delete_meeting(client_app, authenticated_user, meeting, bbb_response):
    res = client_app.post("/meeting/delete", {"id": meeting.id})
    assert ("success", "Élément supprimé") in res.flashes
    assert len(Meeting.query.all()) == 0


def test_meeting_link_retrocompatibility(meeting):
    """Old meeting links must still be usable for long lasting users, and for
    links since 1.2.0.

    https://github.com/numerique-gouv/b3desk/issues/128
    """

    old_hashed_moderator_meeting = hashlib.sha1(
        f"meeting-persistent-{meeting.id}--{meeting.user.hash}|attendee|meeting|moderator".encode()
    ).hexdigest()
    assert meeting.get_role(old_hashed_moderator_meeting) == Role.moderator
    new_hashed_moderator_meeting = hashlib.sha1(
        f"meeting-persistent-{meeting.id}--{meeting.user.hash}|attendee|meeting|{Role.moderator}".encode()
    ).hexdigest()
    assert meeting.get_role(new_hashed_moderator_meeting) == Role.moderator

    old_hashed_attendee_meeting = hashlib.sha1(
        f"meeting-persistent-{meeting.id}--{meeting.user.hash}|attendee|meeting|attendee".encode()
    ).hexdigest()
    assert meeting.get_role(old_hashed_attendee_meeting) == Role.attendee
    new_hashed_attendee_meeting = hashlib.sha1(
        f"meeting-persistent-{meeting.id}--{meeting.user.hash}|attendee|meeting|{Role.attendee}".encode()
    ).hexdigest()
    assert meeting.get_role(new_hashed_attendee_meeting) == Role.attendee

    old_hashed_authenticated_meeting = hashlib.sha1(
        f"meeting-persistent-{meeting.id}--{meeting.user.hash}|attendee|meeting|authenticated".encode()
    ).hexdigest()
    assert meeting.get_role(old_hashed_authenticated_meeting) == Role.authenticated
    new_hashed_authenticated_meeting = hashlib.sha1(
        f"meeting-persistent-{meeting.id}--{meeting.user.hash}|attendee|meeting|{Role.authenticated}".encode()
    ).hexdigest()
    assert meeting.get_role(new_hashed_authenticated_meeting) == Role.authenticated


def test_meeting_order_default(
    client_app, authenticated_user, meeting, meeting_2, meeting_3, bbb_response
):
    response = client_app.get("/welcome", status=200)
    assert response.context["meetings"] == [meeting_3, meeting_2, meeting]


def test_meeting_order_alpha_asc(
    client_app, authenticated_user, meeting, meeting_2, meeting_3, bbb_response
):
    response = client_app.get(
        "/welcome?order-key=name&reverse-order=false&favorite-filter=false", status=200
    )
    assert response.context["meetings"] == [meeting_2, meeting, meeting_3]


def test_meeting_order_alpha_desc(
    client_app, authenticated_user, meeting, meeting_2, meeting_3, bbb_response
):
    response = client_app.get(
        "/welcome?order-key=name&reverse-order=true&favorite-filter=false", status=200
    )
    assert response.context["meetings"] == [meeting_3, meeting, meeting_2]


def test_meeting_order_date_desc(
    client_app, authenticated_user, meeting, meeting_2, meeting_3, bbb_response
):
    response = client_app.get(
        "/welcome?order-key=created_at&reverse-order=true&favorite-filter=false",
        status=200,
    )
    assert response.context["meetings"] == [meeting_3, meeting_2, meeting]


def test_meeting_order_date_asc(
    client_app, authenticated_user, meeting, meeting_2, meeting_3, bbb_response
):
    response = client_app.get(
        "/welcome?order-key=created_at&reverse-order=false&favorite-filter=false",
        status=200,
    )
    assert response.context["meetings"] == [meeting, meeting_2, meeting_3]


def test_favorite_meeting_order_alpha_asc(
    client_app, authenticated_user, meeting, meeting_2, meeting_3, bbb_response
):
    response = client_app.get(
        "/welcome?order-key=name&reverse-order=false&favorite-filter=true", status=200
    )
    assert response.context["meetings"] == [meeting_2, meeting]


def test_favorite_meeting_order_alpha_desc(
    client_app, authenticated_user, meeting, meeting_2, meeting_3, bbb_response
):
    response = client_app.get(
        "/welcome?order-key=name&reverse-order=true&favorite-filter=true", status=200
    )
    assert response.context["meetings"] == [meeting, meeting_2]


def test_favorite_meeting_order_date_desc(
    client_app, authenticated_user, meeting, meeting_2, meeting_3, bbb_response
):
    response = client_app.get(
        "/welcome?order-key=created_at&reverse-order=true&favorite-filter=true",
        status=200,
    )
    assert response.context["meetings"] == [meeting_2, meeting]


def test_favorite_meeting_order_date_asc(
    client_app, authenticated_user, meeting, meeting_2, meeting_3, bbb_response
):
    response = client_app.get(
        "/welcome?order-key=created_at&reverse-order=false&favorite-filter=true",
        status=200,
    )
    assert response.context["meetings"] == [meeting, meeting_2]


def test_add_and_remove_favorite(
    client_app, authenticated_user, meeting, meeting_2, meeting_3, bbb_response
):
    assert not meeting_3.is_favorite
    response = client_app.post(
        "/meeting/favorite?order-key=created_at&reverse-order=true&favorite-filter=true",
        {"id": meeting_3.id},
    ).follow()
    assert response.context["meetings"] == [meeting_3, meeting_2, meeting]
    assert meeting_3.is_favorite

    response = client_app.post(
        "/meeting/favorite?order-key=created_at&reverse-order=true&favorite-filter=true",
        {"id": meeting_3.id},
    ).follow()
    assert response.context["meetings"] == [meeting_2, meeting]
    assert not meeting_3.is_favorite


def test_add_favorite_by_wrong_user_failed(
    client_app, bbb_response, authenticated_user_2, meeting, meeting_2, meeting_3
):
    response = client_app.get("/welcome", status=200)
    response.mustcontain("Berenice Cooler")
    response = client_app.post("/meeting/favorite", {"id": meeting_3.id}, status=403)

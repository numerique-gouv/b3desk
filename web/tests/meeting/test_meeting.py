import datetime
import hashlib
import time
from datetime import date
from pathlib import Path
from unittest import mock
from urllib.parse import parse_qs
from urllib.parse import urlparse

from b3desk.endpoints.bbb_callback import get_recording_status_callback_url
from b3desk.join import get_meeting_secret_key
from b3desk.join import get_quick_meeting_secret_key
from b3desk.join import get_role
from b3desk.models import db
from b3desk.models.meetings import MODERATOR_ONLY_MESSAGE_MAXLENGTH
from b3desk.models.meetings import Meeting
from b3desk.models.meetings import MeetingFiles
from b3desk.models.meetings import MeetingSecretKey
from b3desk.models.meetings import assign_unique_voice_bridge
from b3desk.models.meetings import delete_old_voiceBridges
from b3desk.models.meetings import generate_random_pin
from b3desk.models.meetings import get_all_previous_voiceBridges
from b3desk.models.meetings import get_forbidden_pins
from b3desk.models.meetings import get_inactive_meetings_to_inform
from b3desk.models.meetings import get_meeting_by_visio_code
from b3desk.models.meetings import get_meeting_file_hash
from b3desk.models.meetings import get_quick_meeting_from_meeting_id
from b3desk.models.meetings import unique_visio_code_generation
from b3desk.models.meetings import visio_code_exists
from b3desk.models.roles import Role
from b3desk.tasks import delete_old_meetings
from b3desk.tasks import inform_owner_before_meeting_deletion
from b3desk.utils.mailing import DELAY_FOR_FIRST_EMAIL
from b3desk.utils.mailing import DELAY_FOR_SECOND_EMAIL
from b3desk.utils.mailing import DELAY_FOR_THIRD_EMAIL
from flask import url_for


def test_show_meeting_recording(client_app, authenticated_user, meeting, bbb_response):
    """Test that meeting recordings page displays correctly."""
    response = client_app.get(f"/meeting/recordings/{meeting.id}", status=200)

    assert "meeting/recordings.html" in response.contexts


def test_new_meeting(client_app, authenticated_user):
    """Test that new meeting form displays correctly."""
    response = client_app.get("/meeting/new", status=200)

    assert response.template == "meeting/wizard.html"


def test_new_meeting_when_recording_not_configured(client_app, authenticated_user):
    """Test that recording options are hidden when recording is disabled."""
    client_app.app.config["RECORDING"] = False

    response = client_app.get("/meeting/new")

    response.mustcontain(no="Enregistrement")


def test_edit_meeting(client_app, authenticated_user, meeting, bbb_response):
    """Test that meeting edit form displays correctly."""
    response = client_app.get(f"/meeting/edit/{meeting.id}", status=200)

    assert response.template == "meeting/wizard.html"


def test_save_new_meeting(
    client_app, authenticated_user, mock_meeting_is_not_running, caplog
):
    """Test that new meeting can be created with all settings."""
    res = client_app.get("/meeting/new")
    res.forms[0]["name"] = "Mon meeting de test"
    res.forms[0]["welcome"] = "Bienvenue dans mon meeting de test"
    res.forms[0]["maxParticipants"] = 5
    res.forms[0]["duration"] = 60
    res.forms[0]["guestPolicy"] = "on"
    res.forms[0]["webcamsOnlyForModerator"] = "on"
    res.forms[0]["muteOnStart"] = "on"
    res.forms[0]["lockSettingsDisableCam"] = False
    res.forms[0]["lockSettingsDisableMic"] = False
    res.forms[0]["lockSettingsDisablePrivateChat"] = False
    res.forms[0]["lockSettingsDisablePublicChat"] = False
    res.forms[0]["lockSettingsDisableNote"] = False
    res.forms[0]["moderatorOnlyMessage"] = "Bienvenue aux modérateurs"
    res.forms[0]["logoutUrl"] = "https://log.out"
    res.forms[0]["moderatorPW"] = "Motdepasse1"
    res.forms[0]["attendeePW"] = "Motdepasse2"
    res.forms[0]["autoStartRecording"] = "on"
    res.forms[0]["allowStartStopRecording"] = "on"
    res.forms[0]["voiceBridge"] = "123456789"

    res = res.forms[0].submit()
    assert (
        "success",
        "Mon meeting de test a bien été créé(e)",
    ) in res.flashes

    meetings = db.session.scalars(db.select(Meeting)).all()
    meeting = meetings[0]

    assert meeting.owner_id == 1
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
    assert meeting.voiceBridge == "123456789"
    assert len(meeting.visio_code) == 9
    assert meeting.visio_code.isdigit()
    assert (
        f"Meeting Mon meeting de test {meeting.id} was created by alice@domain.tld\n"
        in caplog.text
    )


def test_save_existing_meeting_not_running(
    client_app, authenticated_user, meeting, mock_meeting_is_not_running, caplog
):
    """Test that existing meeting can be updated when not running."""
    assert db.session.scalar(db.select(db.func.count()).select_from(Meeting)) == 1

    res = client_app.get(f"/meeting/edit/{meeting.id}")
    res.forms[0]["name"] = "Mon meeting de test"
    res.forms[0]["welcome"] = "Bienvenue dans mon meeting de test"
    res.forms[0]["maxParticipants"] = 5
    res.forms[0]["duration"] = 60
    res.forms[0]["guestPolicy"] = "on"
    res.forms[0]["webcamsOnlyForModerator"] = "on"
    res.forms[0]["muteOnStart"] = "on"
    res.forms[0]["lockSettingsDisableCam"] = False
    res.forms[0]["lockSettingsDisableMic"] = False
    res.forms[0]["lockSettingsDisablePrivateChat"] = False
    res.forms[0]["lockSettingsDisablePublicChat"] = False
    res.forms[0]["lockSettingsDisableNote"] = False
    res.forms[0]["moderatorOnlyMessage"] = "Bienvenue aux modérateurs"
    res.forms[0]["logoutUrl"] = "https://log.out"
    res.forms[0]["moderatorPW"] = "Motdepasse1"
    res.forms[0]["attendeePW"] = "Motdepasse2"
    res.forms[0]["autoStartRecording"] = "on"
    res.forms[0]["allowStartStopRecording"] = "on"
    res.forms[0]["voiceBridge"] = "123456789"

    res = res.forms[0].submit()
    assert ("success", "meeting modifications prises en compte") in res.flashes

    meetings = db.session.scalars(db.select(Meeting)).all()
    assert len(meetings) == 1
    meeting = meetings[0]

    assert meeting.owner_id == 1
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
    assert meeting.voiceBridge == "123456789"
    data = "{'welcome': 'Bienvenue dans mon meeting de test', 'maxParticipants': 5, 'duration': 60, 'moderatorOnlyMessage': 'Bienvenue aux modérateurs', 'logoutUrl': 'https://log.out', 'moderatorPW': 'Motdepasse1', 'attendeePW': 'Motdepasse2', 'voiceBridge': '123456789'}"
    assert (
        f"Meeting meeting {meeting.id} was updated by alice@domain.tld. Updated fields : {data}\n"
        in caplog.text
    )


def test_edit_meeting_moderatorPW_change_renews_moderator_secret_key(
    client_app, authenticated_user, meeting, mock_meeting_is_not_running, caplog
):
    """Changing moderatorPW must renew only the moderator secret key, clearing its legacy hashes."""
    moderator_secret_key = db.session.scalars(
        db.select(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.role == Role.moderator.name,
        )
    ).one()
    attendee_secret_key = db.session.scalars(
        db.select(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.role == Role.attendee.name,
        )
    ).one()
    authenticated_secret_key = db.session.scalars(
        db.select(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.role == Role.authenticated.name,
        )
    ).one()
    moderator_secret_key.legacy_secret_keys = ["old-moderator-hash"]
    db.session.commit()

    previous_moderator_secret = moderator_secret_key.secret_key
    previous_attendee_secret = attendee_secret_key.secret_key
    previous_authenticated_secret = authenticated_secret_key.secret_key

    res = client_app.get(f"/meeting/edit/{meeting.id}")
    res.forms[0]["moderatorPW"] = "NewModeratorPW1"
    res.forms[0].submit()

    db.session.refresh(moderator_secret_key)
    db.session.refresh(attendee_secret_key)
    db.session.refresh(authenticated_secret_key)

    assert moderator_secret_key.secret_key != previous_moderator_secret
    assert moderator_secret_key.legacy_secret_keys == []
    assert attendee_secret_key.secret_key == previous_attendee_secret
    assert authenticated_secret_key.secret_key == previous_authenticated_secret
    assert (
        f"Meeting meeting {meeting.id}: moderatorPW changed by alice@domain.tld, moderator secret key renewed"
        in caplog.text
    )


def test_edit_meeting_attendeePW_change_renews_attendee_and_authenticated_secret_keys(
    client_app, authenticated_user, meeting, mock_meeting_is_not_running, caplog
):
    """Changing attendeePW must renew the attendee and authenticated secret keys, clearing their legacy hashes, but not moderator's."""
    moderator_secret_key = db.session.scalars(
        db.select(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.role == Role.moderator.name,
        )
    ).one()
    attendee_secret_key = db.session.scalars(
        db.select(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.role == Role.attendee.name,
        )
    ).one()
    authenticated_secret_key = db.session.scalars(
        db.select(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.role == Role.authenticated.name,
        )
    ).one()
    attendee_secret_key.legacy_secret_keys = ["old-attendee-hash"]
    authenticated_secret_key.legacy_secret_keys = ["old-authenticated-hash"]
    db.session.commit()

    previous_moderator_secret = moderator_secret_key.secret_key
    previous_attendee_secret = attendee_secret_key.secret_key
    previous_authenticated_secret = authenticated_secret_key.secret_key

    res = client_app.get(f"/meeting/edit/{meeting.id}")
    res.forms[0]["attendeePW"] = "NewAttendeePW1"
    res.forms[0].submit()

    db.session.refresh(moderator_secret_key)
    db.session.refresh(attendee_secret_key)
    db.session.refresh(authenticated_secret_key)

    assert attendee_secret_key.secret_key != previous_attendee_secret
    assert attendee_secret_key.legacy_secret_keys == []
    assert authenticated_secret_key.secret_key != previous_authenticated_secret
    assert authenticated_secret_key.legacy_secret_keys == []
    assert moderator_secret_key.secret_key == previous_moderator_secret
    assert (
        f"Meeting meeting {meeting.id}: attendeePW changed by alice@domain.tld, attendee and authenticated secret keys renewed"
        in caplog.text
    )


def test_edit_meeting_changing_both_passwords_renews_all_secret_keys(
    client_app, authenticated_user, meeting, mock_meeting_is_not_running, caplog
):
    """Changing both moderatorPW and attendeePW must renew every role's secret key."""
    moderator_secret_key = db.session.scalars(
        db.select(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.role == Role.moderator.name,
        )
    ).one()
    attendee_secret_key = db.session.scalars(
        db.select(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.role == Role.attendee.name,
        )
    ).one()
    authenticated_secret_key = db.session.scalars(
        db.select(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.role == Role.authenticated.name,
        )
    ).one()
    previous_moderator_secret = moderator_secret_key.secret_key
    previous_attendee_secret = attendee_secret_key.secret_key
    previous_authenticated_secret = authenticated_secret_key.secret_key

    res = client_app.get(f"/meeting/edit/{meeting.id}")
    res.forms[0]["moderatorPW"] = "NewModeratorPW1"
    res.forms[0]["attendeePW"] = "NewAttendeePW1"
    res.forms[0].submit()

    db.session.refresh(moderator_secret_key)
    db.session.refresh(attendee_secret_key)
    db.session.refresh(authenticated_secret_key)

    assert moderator_secret_key.secret_key != previous_moderator_secret
    assert attendee_secret_key.secret_key != previous_attendee_secret
    assert authenticated_secret_key.secret_key != previous_authenticated_secret
    assert (
        f"Meeting meeting {meeting.id}: moderatorPW changed by alice@domain.tld, moderator secret key renewed"
        in caplog.text
    )
    assert (
        f"Meeting meeting {meeting.id}: attendeePW changed by alice@domain.tld, attendee and authenticated secret keys renewed"
        in caplog.text
    )


def test_save_existing_meeting_running(
    mocker, client_app, authenticated_user, meeting, mock_meeting_is_running
):
    """Test that existing meeting can be updated and ended when running."""
    mocker.patch("b3desk.models.bbb.BBB.end", return_value={"returncode": "SUCCESS"})
    assert db.session.scalar(db.select(db.func.count()).select_from(Meeting)) == 1

    res = client_app.get(f"/meeting/edit/{meeting.id}")
    res.forms[0]["welcome"] = "Bienvenue dans mon meeting de test"

    res = res.forms[0].submit()
    assert res.template == "meeting/end.html"
    assert "Vous n'êtes pas propriétaire" not in res
    assert ("success", "meeting modifications prises en compte") in res.flashes

    meetings = db.session.scalars(db.select(Meeting)).all()
    assert len(meetings) == 1
    meeting = meetings[0]
    assert meeting.welcome == "Bienvenue dans mon meeting de test"

    res = res.forms[0].submit()
    assert ("success", "Séminaire « meeting » terminé") in res.flashes


def test_save_moderatorOnlyMessage_too_long(
    client_app, authenticated_user, mock_meeting_is_not_running
):
    """Test that validation fails when moderator message is too long."""
    res = client_app.get("/meeting/new")
    moderator_only_message = "a" * (MODERATOR_ONLY_MESSAGE_MAXLENGTH + 1)
    res.forms[0]["moderatorOnlyMessage"] = moderator_only_message
    res = res.forms[0].submit()

    res.mustcontain("Le formulaire contient des erreurs")
    res.mustcontain(moderator_only_message)
    res.mustcontain("Le message est trop long")
    assert db.session.scalar(db.select(db.func.count()).select_from(Meeting)) == 0


def test_save_no_recording_by_default(
    client_app, authenticated_user, mock_meeting_is_not_running
):
    """Test that recording is disabled by default."""
    res = client_app.get("/meeting/new")
    res.forms[0]["name"] = "Mon meeting de test"
    res.forms[0]["maxParticipants"] = 5
    res.forms[0]["duration"] = 60
    res.forms[0]["moderatorPW"] = "Motdepasse1"
    res.forms[0]["attendeePW"] = "Motdepasse2"

    res = res.forms[0].submit()
    assert (
        "success",
        "Mon meeting de test a bien été créé(e)",
    ) in res.flashes

    meetings = db.session.scalars(db.select(Meeting)).all()
    assert len(meetings) == 1
    meeting = meetings[0]
    assert meeting.record is True
    assert meeting.autoStartRecording is False
    assert meeting.allowStartStopRecording is True


def test_save_meeting_in_no_recording_environment(
    client_app, authenticated_user, mock_meeting_is_not_running
):
    """Test that meeting can be created when recording is disabled globally."""
    assert db.session.scalar(db.select(db.func.count()).select_from(Meeting)) == 0
    client_app.app.config["RECORDING"] = False

    res = client_app.get("/meeting/new")
    res.forms[0]["name"] = "Mon meeting de test"
    res.forms[0]["maxParticipants"] = 5
    res.forms[0]["duration"] = 60
    res.forms[0]["moderatorPW"] = "Motdepasse1"
    res.forms[0]["attendeePW"] = "Motdepasse2"

    assert "allowStartStopRecording" not in res.forms[0].fields
    assert "autoStartRecording" not in res.forms[0].fields

    res = res.forms[0].submit()
    assert (
        "success",
        "Mon meeting de test a bien été créé(e)",
    ) in res.flashes

    meetings = db.session.scalars(db.select(Meeting)).all()
    assert len(meetings) == 1
    assert meetings[0].record is False


def test_create_no_file(
    client_app,
    meeting,
    mocker,
    bbb_response,
    mock_meeting_is_not_running,
    authenticated_user,
    user,
):
    """Tests the BBB meeting creation request.

    As there is no file attached to the meeting, no background upload
    task should be called.
    """
    from b3desk.join import create_bbb_meeting

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
    meeting.ai_summary = False
    create_bbb_meeting(meeting, meeting.owner)

    assert bbb_response.called
    bbb_url = bbb_response.call_args.args[0].url
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/create"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }
    body = {
        "meetingID": meeting.bbb_meeting_id,
        "name": "My Meeting",
        "meetingKeepEvents": "true",
        "meta_analytics-callback-url": "https://bbb-analytics.test/v1/post_events",
        "meta_academy": "domain.tld",
        "attendeePW": "Password1",
        "moderatorPW": "Password2",
        "welcome": "Welcome!",
        "maxParticipants": "25",
        "logoutURL": "https://log.out",
        "record": "true",
        "duration": "60",
        "moderatorOnlyMessage": f'Welcome moderators!<br />\n\n    Code de connexion : {meeting.visio_code}<br />\n\n Lien Modérateur   : <a href="{meeting.moderator_url}" target="_blank">{meeting.moderator_url}</a><br />\n\n Lien Participant   : <a href="{meeting.attendee_url}" target="_blank">{meeting.attendee_url}</a>',
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
        "presentationUploadExternalDescription": client_app.app.config[
            "EXTERNAL_UPLOAD_DESCRIPTION"
        ],
        "presentationUploadExternalUrl": url_for(
            "meeting_files.file_picker",
            bbb_meeting_id=meeting.bbb_meeting_id,
            _external=True,
        ),
        "voiceBridge": "111111111",
        "meta_bbb-recording-ready-url": get_recording_status_callback_url(),
        "meta_bbb-disable-recording-formats": "ai-summary",
    }

    assert bbb_params == body

    assert not mocked_background_upload.called


def test_create_ai_summary_adds_banner(
    client_app,
    meeting,
    mocker,
    bbb_response,
    mock_meeting_is_not_running,
    authenticated_user,
    user,
):
    """AI summary enabled adds the banner and keeps the ai-summary format."""
    from b3desk.join import create_bbb_meeting

    meeting.ai_summary = True
    assert meeting.ai_summary_enabled

    create_bbb_meeting(meeting, meeting.owner)

    assert bbb_response.called
    bbb_url = bbb_response.call_args.args[0].url
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }

    assert (
        bbb_params["bannerText"]
        == "⚠️ Les enregistrements de cette session seront traités par l'IA AlbertAPI"
    )
    assert bbb_params["bannerColor"] == "#202c7d"
    assert "meta_bbb-disable-recording-formats" not in bbb_params


def test_create_with_only_a_default_file(
    client_app,
    meeting,
    mocker,
    bbb_response,
    jpg_file_content,
    tmp_path,
    mock_meeting_is_not_running,
):
    """Tests the BBB meeting creation request.

    A default file, which is no longer a real functionnality, attached
    to the meeting, should always be sent asynchronously, background
    upload task should be called.
    """
    from b3desk.join import create_bbb_meeting

    client_app.app.config["FILE_SHARING"] = True

    file_path = str(tmp_path / "foobar.jpg")
    with Path(file_path).open("wb") as fd:
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
    meeting.ai_summary = False

    meeting_file = MeetingFiles(
        nc_path=file_path,
        title="file_title",
        created_at=datetime.date(2024, 3, 19),
        meeting_id=meeting.id,
    )
    meeting_file.owner = meeting.owner
    meeting.files = [meeting_file]

    create_bbb_meeting(meeting, meeting.owner)

    assert bbb_response.called
    bbb_url = bbb_response.call_args.args[0].url
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/create"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }
    body = {
        "meetingID": meeting.bbb_meeting_id,
        "name": "My Meeting",
        "meetingKeepEvents": "true",
        "meta_analytics-callback-url": "https://bbb-analytics.test/v1/post_events",
        "meta_academy": "domain.tld",
        "attendeePW": "Password1",
        "moderatorPW": "Password2",
        "welcome": "Welcome!",
        "maxParticipants": "25",
        "logoutURL": "https://log.out",
        "record": "true",
        "duration": "60",
        "moderatorOnlyMessage": f'Welcome moderators!<br />\n\n    Code de connexion : {meeting.visio_code}<br />\n\n Lien Modérateur   : <a href="{meeting.moderator_url}" target="_blank">{meeting.moderator_url}</a><br />\n\n Lien Participant   : <a href="{meeting.attendee_url}" target="_blank">{meeting.attendee_url}</a>',
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
        "presentationUploadExternalDescription": client_app.app.config[
            "EXTERNAL_UPLOAD_DESCRIPTION"
        ],
        "presentationUploadExternalUrl": url_for(
            "meeting_files.file_picker",
            bbb_meeting_id=meeting.bbb_meeting_id,
            _external=True,
        ),
        "voiceBridge": "111111111",
        "meta_bbb-recording-ready-url": get_recording_status_callback_url(),
        "meta_bbb-disable-recording-formats": "ai-summary",
    }

    assert bbb_params == body

    assert mocked_background_upload.called


def test_create_with_files(
    client_app,
    meeting,
    mocker,
    bbb_response,
    jpg_file_content,
    tmp_path,
    mock_meeting_is_not_running,
):
    """Tests the BBB meeting creation request.

    As there is a non default file attached to the meeting, the
    background upload task should be called.
    """
    from b3desk.join import create_bbb_meeting

    client_app.app.config["FILE_SHARING"] = True

    file_path = str(tmp_path / "foobar.jpg")
    with Path(file_path).open("wb") as fd:
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
    meeting.meta_recording_recording_ai_summary = True

    meeting_file = MeetingFiles(
        nc_path=file_path,
        title="file_title",
        created_at=datetime.date(2024, 3, 19),
        meeting_id=meeting.id,
    )
    meeting_file.owner = meeting.owner
    meeting.files = [meeting_file]

    create_bbb_meeting(meeting, meeting.owner)

    assert bbb_response.called
    bbb_url = bbb_response.call_args.args[0].url
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/create"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }

    body = {
        "meetingID": meeting.bbb_meeting_id,
        "name": "My Meeting",
        "meetingKeepEvents": "true",
        "meta_analytics-callback-url": "https://bbb-analytics.test/v1/post_events",
        "meta_academy": "domain.tld",
        "attendeePW": "Password1",
        "moderatorPW": "Password2",
        "welcome": "Welcome!",
        "maxParticipants": "25",
        "logoutURL": "https://log.out",
        "record": "true",
        "duration": "60",
        "moderatorOnlyMessage": f'Welcome moderators!<br />\n\n    Code de connexion : {meeting.visio_code}<br />\n\n Lien Modérateur   : <a href="{meeting.moderator_url}" target="_blank">{meeting.moderator_url}</a><br />\n\n Lien Participant   : <a href="{meeting.attendee_url}" target="_blank">{meeting.attendee_url}</a>',
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
        "presentationUploadExternalDescription": client_app.app.config[
            "EXTERNAL_UPLOAD_DESCRIPTION"
        ],
        "presentationUploadExternalUrl": url_for(
            "meeting_files.file_picker",
            bbb_meeting_id=meeting.bbb_meeting_id,
            _external=True,
        ),
        "voiceBridge": "111111111",
        "meta_bbb-recording-ready-url": get_recording_status_callback_url(),
        "meta_bbb-disable-recording-formats": "ai-summary",
    }

    assert bbb_params == body
    assert mocked_background_upload.called
    assert mocked_background_upload.call_args.args[0].startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/insertDocument"
    )

    filehash = get_meeting_file_hash(meeting.owner.id, meeting_file.nc_path)

    xml_content = mocked_background_upload.call_args.args[1]
    assert xml_content.startswith(
        f"<?xml version='1.0' encoding='UTF-8'?> <modules>  <module name='presentation'> <document downloadable='false' url='http://b3desk.test/ncdownload/{filehash}/{meeting.owner.id}/"
    )
    assert xml_content.endswith(
        f"{tmp_path.name}/foobar.jpg' filename='file_title' /> </module></modules>"
    )


def test_create_without_logout_url_gets_default(
    app, client_app, authenticated_user, mock_meeting_is_not_running
):
    """Test that default logout URL is used when none specified."""
    res = client_app.get("/meeting/new")
    res = res.forms[0].submit()
    assert ("success", "Mon séminaire a bien été créé(e)") in res.flashes

    meetings = db.session.scalars(db.select(Meeting)).all()
    assert len(meetings) == 1
    meeting = meetings[0]
    assert meeting
    assert meeting.logoutUrl == app.config["MEETING_LOGOUT_URL"]


def test_save_existing_meeting_gets_default_logoutUrl(
    client_app,
    authenticated_user,
    meeting,
    mocker,
    bbb_response,
    mock_meeting_is_not_running,
):
    """Test that empty logout URL gets replaced with default."""
    from b3desk.join import create_bbb_meeting

    assert db.session.scalar(db.select(db.func.count()).select_from(Meeting)) == 1

    res = client_app.get(f"/meeting/edit/{meeting.id}")
    res.forms[0]["logoutUrl"] = ""
    res = res.forms[0].submit()
    assert ("success", "meeting modifications prises en compte") in res.flashes

    meetings = db.session.scalars(db.select(Meeting)).all()
    assert len(meetings) == 1
    meeting = meetings[0]

    create_bbb_meeting(meeting, meeting.owner)

    assert bbb_response.called
    bbb_url = bbb_response.call_args.args[0].url
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/create"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }
    assert bbb_params.get("logoutURL", "") == client_app.app.config.get(
        "MEETING_LOGOUT_URL"
    )


def test_create_and_join_quick_meeting(
    client_app,
    authenticated_user,
    mocker,
    bbb_response,
    mock_meeting_is_not_running,
    caplog,
):
    """Test user can create and join a quick meeting."""
    res = client_app.get("/meeting/quick", status=302)
    assert "https://bbb.test/join?fullName=Alice+Cooper&meetingID=" in res.location
    assert (
        "creation result: {'returncode': 'SUCCESS', 'running': 'true', 'voiceBridge': '111111111', 'attendeePW': 'attendee', 'moderatorPW': 'moderator'}"
        in caplog.text
    )


def test_create_quick_meeting(
    client_app, monkeypatch, user, mocker, bbb_response, mock_meeting_is_not_running
):
    """Test that quick meeting is created with correct default parameters."""
    from b3desk.endpoints.meetings import get_quick_meeting_from_meeting_id
    from b3desk.join import create_bbb_quick_meeting
    from b3desk.models.meetings import get_deterministic_password

    mocker.patch("b3desk.tasks.background_upload.delay", return_value=True)
    monkeypatch.setattr("b3desk.models.users.User.id", 1)
    monkeypatch.setattr("b3desk.models.users.User.hash", "hash")
    meeting = get_quick_meeting_from_meeting_id()

    expected_attendee_pw = get_deterministic_password(meeting.id, "attendee")
    expected_moderator_pw = get_deterministic_password(meeting.id, "moderator")
    expected_moderator_hash = get_quick_meeting_secret_key(meeting, Role.moderator)
    expected_attendee_hash = get_quick_meeting_secret_key(meeting, Role.attendee)
    create_bbb_quick_meeting(meeting, user)

    assert bbb_response.called
    bbb_url = bbb_response.call_args.args[0].url
    assert bbb_url.startswith(
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/create"
    )
    bbb_params = {
        key: value[0] for key, value in parse_qs(urlparse(bbb_url).query).items()
    }
    assert bbb_params == {
        "meetingID": meeting.bbb_meeting_id,
        "name": "Séminaire improvisé",
        "attendeePW": expected_attendee_pw,
        "moderatorPW": expected_moderator_pw,
        "logoutURL": "http://quick-meeting-logout.test/",
        "duration": "280",
        "meetingKeepEvents": "true",
        "meta_analytics-callback-url": "https://bbb-analytics.test/v1/post_events",
        "meta_academy": "domain.tld",
        "moderatorOnlyMessage": f'Bienvenue aux modérateurs. Pour inviter quelqu\'un à ce séminaire, envoyez-lui l\'un de ces liens :<br />\n\n Lien Modérateur  \u00a0: <a href="http://b3desk.test/meeting/signin/moderateur/{meeting.id}/hash/{expected_moderator_hash}" target="_blank">http://b3desk.test/meeting/signin/moderateur/{meeting.id}/hash/{expected_moderator_hash}</a><br />\n\n Lien Participant  \u00a0: <a href="http://b3desk.test/meeting/signin/invite/{meeting.id}/hash/{expected_attendee_hash}" target="_blank">http://b3desk.test/meeting/signin/invite/{meeting.id}/hash/{expected_attendee_hash}</a>',
        "voiceBridge": mock.ANY,
        "guestPolicy": "ALWAYS_ACCEPT",
        "checksum": mock.ANY,
        "presentationUploadExternalDescription": "Fichiers depuis votre Nextcloud",
        "presentationUploadExternalUrl": mock.ANY,
        "meta_bbb-disable-recording-formats": "ai-summary",
    }


def test_join_meeting_as_moderator_quick_meeting(client_app, bbb_response):
    """Test moderator joining a non-existent meeting creates a quick BBB meeting."""
    quick_meeting = get_quick_meeting_from_meeting_id()
    moderator_hash = get_quick_meeting_secret_key(quick_meeting, Role.moderator)
    response = client_app.get(
        f"/meeting/signin/{quick_meeting.id}/hash/{moderator_hash}"
    )
    response.form["fullname"] = "Alice"
    response = response.form.submit()

    assert bbb_response.called
    assert (
        f"{client_app.app.config['BIGBLUEBUTTON_ENDPOINT']}/join" in response.location
    )


def test_edit_files_meeting(client_app, authenticated_user, meeting, bbb_response):
    """Test that meeting files edit page displays correctly."""
    client_app.app.config["FILE_SHARING"] = True

    response = client_app.get(f"/meeting/files/{meeting.id}", status=200)

    assert response.template == "meeting/filesform.html"


def test_deactivated_meeting_files_cannot_access_files(
    client_app, authenticated_user, meeting, bbb_response
):
    """Test that file sharing link is hidden when feature is disabled."""
    client_app.app.config["FILE_SHARING"] = False

    response = client_app.get("/welcome", status=200)

    response.mustcontain(no="Fichiers associés à ")


def test_deactivated_meeting_files_cannot_edit(
    client_app, authenticated_user, meeting, bbb_response
):
    """Test that file edit page is inaccessible when feature is disabled."""
    client_app.app.config["FILE_SHARING"] = False

    response = client_app.get(f"/meeting/files/{meeting.id}", status=302)

    assert "welcome" in response.location


def test_delete_meeting(client_app, authenticated_user, meeting, bbb_response):
    """Test that meeting can be deleted, its secret keys are removed and voiceBridge is archived."""
    assert db.session.scalar(
        db.select(db.func.count()).select_from(MeetingSecretKey)
    ) == len(Role)

    res = client_app.post("/meeting/delete", {"id": meeting.id})
    assert ("success", "Élément supprimé") in res.flashes
    assert db.session.scalar(db.select(db.func.count()).select_from(Meeting)) == 0
    assert (
        db.session.scalar(db.select(db.func.count()).select_from(MeetingSecretKey)) == 0
    )
    previous_voiceBridges = get_all_previous_voiceBridges()
    assert len(previous_voiceBridges) == 1
    assert previous_voiceBridges[0] == "111111111"


def test_delete_meeting_with_meeting_files(
    client_app, authenticated_user, meeting, bbb_response
):
    """Test that meeting can be deleted even if there is meeting files, and that the files are deleted too."""
    meeting_file = MeetingFiles(
        url="https://example.com/doc.pdf",
        title="doc.pdf",
        created_at=date.today(),
        meeting_id=meeting.id,
        owner=meeting.owner,
    )
    db.session.add(meeting_file)
    db.session.commit()
    res = client_app.post("/meeting/delete", {"id": meeting.id})
    assert ("success", "Élément supprimé") in res.flashes
    assert db.session.scalar(db.select(db.func.count()).select_from(Meeting)) == 0
    assert db.session.scalar(db.select(db.func.count()).select_from(MeetingFiles)) == 0
    previous_voiceBridges = get_all_previous_voiceBridges()
    assert len(previous_voiceBridges) == 1
    assert previous_voiceBridges[0] == "111111111"


def test_meeting_link_retrocompatibility(meeting):
    """Links from meetings migrated from the old hash scheme must stay usable."""
    for role in Role:
        meeting_secret_key = db.session.scalars(
            db.select(MeetingSecretKey).where(
                MeetingSecretKey.meeting_id == meeting.id,
                MeetingSecretKey.role == role.name,
            )
        ).one()
        role_interpolated_raw = hashlib.sha1(
            f"{meeting.bbb_meeting_id}|{meeting.attendeePW}|{meeting.name}|{role}".encode()
        ).hexdigest()
        role_interpolated_as_name = hashlib.sha1(
            f"{meeting.bbb_meeting_id}|{meeting.attendeePW}|{meeting.name}|{role.name}".encode()
        ).hexdigest()
        meeting_secret_key.legacy_secret_keys = [
            role_interpolated_raw,
            role_interpolated_as_name,
        ]
        db.session.commit()

        assert get_role(meeting, role_interpolated_raw) == role
        assert get_role(meeting, role_interpolated_as_name) == role

    assert get_role(meeting, "some-hash-never-generated-for-this-meeting") is None


def test_quick_meeting_link_retrocompatibility(client_app):
    """Links handed out before quick meetings had UUID identifiers must stay usable."""
    legacy_id = "abcd1234"
    meeting = get_quick_meeting_from_meeting_id(legacy_id)
    name = str(client_app.app.config["QUICK_MEETING_DEFAULT_NAME"])

    assert meeting.bbb_meeting_id == f"meeting-vanish-{legacy_id}--"

    for role in Role:
        legacy_secret_key = hashlib.sha1(
            f"meeting-vanish-{legacy_id}--|{meeting.attendeePW}|{name}|{role}".encode()
        ).hexdigest()
        assert get_role(meeting, legacy_secret_key) == role

    assert get_role(meeting, "some-hash-never-generated-for-this-meeting") is None


def test_meeting_order_default(
    client_app,
    authenticated_user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    bbb_response,
):
    """Test that meetings are ordered by creation date descending by default."""
    response = client_app.get("/welcome", status=200)
    assert response.context["meetings"] == [meeting_3, meeting_2, meeting]


def test_meeting_order_alpha_asc(
    client_app,
    authenticated_user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    bbb_response,
):
    """Test that meetings can be ordered alphabetically ascending."""
    response = client_app.get(
        "/welcome?order_key=name&reverse_order=false&favorite_filter=false", status=200
    )
    assert response.context["meetings"] == [meeting_2, meeting, meeting_3]


def test_meeting_order_alpha_desc(
    client_app,
    authenticated_user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    bbb_response,
):
    """Test that meetings can be ordered alphabetically descending."""
    response = client_app.get(
        "/welcome?order_key=name&reverse_order=true&favorite_filter=false", status=200
    )
    assert response.context["meetings"] == [meeting_3, meeting, meeting_2]


def test_meeting_order_date_desc(
    client_app,
    authenticated_user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    bbb_response,
):
    """Test that meetings can be ordered by creation date descending."""
    response = client_app.get(
        "/welcome?order_key=created_at&reverse_order=true&favorite_filter=false",
        status=200,
    )
    assert response.context["meetings"] == [meeting_3, meeting_2, meeting]


def test_meeting_order_date_asc(
    client_app,
    authenticated_user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    bbb_response,
):
    """Test that meetings can be ordered by creation date ascending."""
    response = client_app.get(
        "/welcome?order_key=created_at&reverse_order=false&favorite_filter=false",
        status=200,
    )
    assert response.context["meetings"] == [meeting, meeting_2, meeting_3]


def test_favorite_meeting_order_alpha_asc(
    client_app,
    authenticated_user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    bbb_response,
):
    """Test that favorite meetings can be ordered alphabetically ascending."""
    response = client_app.get(
        "/welcome?order_key=name&reverse_order=false&favorite_filter=true", status=200
    )
    assert response.context["meetings"] == [meeting_2, meeting]


def test_favorite_meeting_order_alpha_desc(
    client_app,
    authenticated_user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    bbb_response,
):
    """Test that favorite meetings can be ordered alphabetically descending."""
    response = client_app.get(
        "/welcome?order_key=name&reverse_order=true&favorite_filter=true", status=200
    )
    assert response.context["meetings"] == [meeting, meeting_2]


def test_favorite_meeting_order_date_desc(
    client_app,
    authenticated_user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    bbb_response,
):
    """Test that favorite meetings can be ordered by creation date descending."""
    response = client_app.get(
        "/welcome?order_key=created_at&reverse_order=true&favorite_filter=true",
        status=200,
    )
    assert response.context["meetings"] == [meeting_2, meeting]


def test_favorite_meeting_order_date_asc(
    client_app,
    authenticated_user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    bbb_response,
):
    """Test that favorite meetings can be ordered by creation date ascending."""
    response = client_app.get(
        "/welcome?order_key=created_at&reverse_order=false&favorite_filter=true",
        status=200,
    )
    assert response.context["meetings"] == [meeting, meeting_2]


def test_add_and_remove_favorite(
    client_app,
    authenticated_user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    bbb_response,
):
    """Test that meetings can be added and removed from favorites."""
    assert authenticated_user not in meeting_3.favorite_of
    response = client_app.post(
        "/meeting/favorite?order_key=created_at&reverse_order=true&favorite_filter=true",
        {"id": meeting_3.id},
    ).follow()
    assert response.context["meetings"] == [meeting_3, meeting_2, meeting]
    assert authenticated_user in meeting_3.favorite_of

    response = client_app.post(
        "/meeting/favorite?order_key=created_at&reverse_order=true&favorite_filter=true",
        {"id": meeting_3.id},
    ).follow()
    assert response.context["meetings"] == [meeting_2, meeting]
    assert authenticated_user not in meeting_3.favorite_of


def test_create_meeting_with_wrong_PIN(
    client_app, meeting, authenticated_user, mock_meeting_is_not_running, bbb_response
):
    """Test that invalid PIN formats are rejected with appropriate error messages."""
    client_app.app.config["ENABLE_PIN_MANAGEMENT"] = True

    res = client_app.get("/meeting/new")
    res.forms[0]["name"] = "Mon meeting de test"
    res.forms[0]["voiceBridge"] = "1234567890"
    res = res.forms[0].submit()
    res.mustcontain("Entez un PIN de 9 chiffres")
    res.forms[0]["voiceBridge"] = "12345678"
    res = res.forms[0].submit()
    res.mustcontain("Entez un PIN de 9 chiffres")
    res.forms[0]["voiceBridge"] = "a12345678"
    res = res.forms[0].submit()
    res.mustcontain("Le code PIN est composé de chiffres uniquement")
    res.forms[0]["voiceBridge"] = "12azer;:!"
    res = res.forms[0].submit()
    res.mustcontain("Le code PIN est composé de chiffres uniquement")
    res.forms[0]["voiceBridge"] = "012345678"
    res = res.forms[0].submit()
    res.mustcontain("Le premier chiffre doit être différent de 0")
    res.forms[0]["voiceBridge"] = "111111111"
    res = res.forms[0].submit()
    res.mustcontain("Ce code PIN est déjà utilisé")

    res = client_app.post("/meeting/delete", {"id": meeting.id})
    assert ("success", "Élément supprimé") in res.flashes
    assert db.session.scalar(db.select(db.func.count()).select_from(Meeting)) == 0
    previous_voiceBridges = get_all_previous_voiceBridges()
    assert len(previous_voiceBridges) == 1
    assert previous_voiceBridges[0] == "111111111"
    res = client_app.get("/meeting/new")
    res.forms[0]["voiceBridge"] = "111111111"
    res = res.forms[0].submit()
    res.mustcontain("Ce code PIN est déjà utilisé")


def test_generate_existing_pin(
    client_app,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    authenticated_user,
    mock_meeting_is_not_running,
    mocker,
):
    """Test that PIN generation retries when suggested PIN already exists."""
    client_app.app.config["ENABLE_PIN_MANAGEMENT"] = True

    # Mock returns existing PINs first, then a free one
    # Fixtures use: 111111111, 111111112, 111111113 (meetings) and 511111111 (shadow)
    mocker.patch(
        "b3desk.models.meetings.random.randint",
        side_effect=[111111111, 111111112, 111111113, 222222222],
    )
    res = client_app.get("/meeting/new")
    res.mustcontain("222222222")


def test_edit_meeting_without_change_anything(client_app, meeting, authenticated_user):
    """Test that meeting can be saved without making any changes."""
    res = client_app.get(f"/meeting/edit/{meeting.id}", status=200)
    res = res.forms[0].submit()
    assert ("success", "meeting modifications prises en compte") in res.flashes


def test_edit_meeting_preserves_ai_summary_when_owner_unauthorised(
    client_app, authenticated_user, meeting, mock_meeting_is_not_running
):
    """Editing a meeting must keep the stored ai_summary preference when the owner has lost authorisation and the field is hidden."""
    meeting.ai_summary = True
    db.session.commit()
    client_app.app.config["ENABLE_AI_SUMMARY"] = False
    assert meeting.owner.can_use_ai_summary is False

    res = client_app.get(f"/meeting/edit/{meeting.id}", status=200)
    assert "ai_summary" not in res.forms[0].fields

    res.forms[0]["name"] = "Titre modifié"
    res.forms[0].submit()

    db.session.refresh(meeting)
    assert meeting.ai_summary is True
    assert meeting.ai_summary_enabled is False


def test_delete_old_voiceBridges_with_form(
    time_machine,
    client_app,
    authenticated_user,
    mock_meeting_is_not_running,
    bbb_response,
    user,
    iam_token,
    iam_server,
    iam_user,
):
    """Test that old voiceBridges are automatically deleted after one year via form submission."""
    client_app.app.config["ENABLE_PIN_MANAGEMENT"] = True
    today = datetime.datetime.now()
    one_year_after = today + datetime.timedelta(days=366)

    res = client_app.get("/meeting/new")
    res.forms[0]["voiceBridge"] = "999999999"
    res = res.forms[0].submit()
    assert ("success", "Mon séminaire a bien été créé(e)") in res.flashes
    meeting = db.session.scalar(db.select(Meeting))
    res = client_app.get("/").follow()
    res = client_app.post("/meeting/delete", {"id": {meeting.id}})
    assert ("success", "Élément supprimé") in res.flashes
    previous_voiceBridges = get_all_previous_voiceBridges()
    assert len(previous_voiceBridges) == 1
    assert previous_voiceBridges[0] == "999999999"

    time_machine.move_to(one_year_after)

    with client_app.session_transaction() as session:
        session["access_token"] = iam_token.access_token
        session["access_token_expires_at"] = ""
        session["current_provider"] = "default"
        session["id_token"] = ""
        session["id_token_jwt"] = ""
        session["last_authenticated"] = "true"
        session["last_session_refresh"] = time.time()
        session["userinfo"] = {
            "email": "alice@domain.tld",
            "family_name": "Cooper",
            "given_name": "Alice",
            "preferred_username": "alice",
        }
        session["refresh_token"] = ""

    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    res = client_app.get("/meeting/new")
    res.forms[0]["voiceBridge"] = "999999999"
    res = res.forms[0].submit()
    res.mustcontain(no="Ce code PIN est déjà utilisé")
    assert ("success", "Mon séminaire a bien été créé(e)") in res.flashes
    previous_voiceBridges = get_all_previous_voiceBridges()
    assert len(previous_voiceBridges) == 0
    assert previous_voiceBridges == []


def test_delete_old_voiceBridges(previous_voiceBridge, time_machine):
    """Test that old voiceBridges are deleted after one year."""
    assert get_all_previous_voiceBridges()
    assert previous_voiceBridge.voiceBridge == "487604786"
    assert previous_voiceBridge.archived_at.date() == datetime.date.today()

    today = datetime.datetime.now()
    one_year_after = today + datetime.timedelta(days=366)

    time_machine.move_to(one_year_after)
    delete_old_voiceBridges()
    assert not get_all_previous_voiceBridges()


def test_get_forbidden_pins(
    previous_voiceBridge, meeting, meeting_2, meeting_3, shadow_meeting
):
    """Test that forbidden PINs include active and archived voiceBridges."""
    assert (
        get_forbidden_pins().sort()
        == [
            meeting_2.voiceBridge,
            meeting.voiceBridge,
            meeting_3.voiceBridge,
            previous_voiceBridge.voiceBridge,
        ].sort()
    )

    assert sorted(get_forbidden_pins(meeting.id)) == sorted(
        [
            meeting_2.voiceBridge,
            meeting_3.voiceBridge,
            previous_voiceBridge.voiceBridge,
            shadow_meeting.voiceBridge,
        ]
    )


def test_generate_random_pin():
    """Test that random PIN generation creates valid 9-digit codes."""
    pin = generate_random_pin()
    assert pin.isdigit()
    assert len(pin) == 9
    assert 100000000 <= int(pin) <= 999999999


def test_unique_visio_code_generation(
    meeting, meeting_2, meeting_3, shadow_meeting, shadow_meeting_2, shadow_meeting_3
):
    """Test that visio code generation creates valid unique 9-digit codes."""
    random_visio_codes = []
    for _ in range(100):
        random_visio_codes.append(unique_visio_code_generation())
    for visio_code in random_visio_codes:
        assert len(visio_code) == 9
        assert visio_code.isdigit()


def test_unique_visio_code_generation_with_collision(client_app, mocker):
    """Test that visio code generation retries on collision."""
    mocker.patch(
        "b3desk.models.meetings.visio_code_exists",
        side_effect=[True, True, False],
    )
    code = unique_visio_code_generation()
    assert len(code) == 9
    assert code.isdigit()


def test_visio_code_exists(
    meeting, meeting_2, meeting_3, shadow_meeting, shadow_meeting_2, shadow_meeting_3
):
    """Test that visio_code_exists correctly checks existing codes."""
    assert visio_code_exists("911111111")
    assert visio_code_exists("911111112")
    assert visio_code_exists("511111111")
    assert not visio_code_exists("000000000")


def test_assign_unique_voice_bridge(client_app, user):
    """Test that assign_unique_voice_bridge assigns a valid unique voice bridge."""
    meeting = Meeting(
        owner=user,
        name="test meeting",
        moderatorPW="moderator",
        attendeePW="attendee",
        visio_code="999999999",
    )
    db.session.add(meeting)
    assign_unique_voice_bridge(meeting)
    db.session.commit()

    assert meeting.voiceBridge is not None
    assert len(meeting.voiceBridge) == 9
    assert meeting.voiceBridge.isdigit()


def test_get_meeting_by_visio_code(meeting):
    """Test that meeting can be retrieved by visio code."""
    meeting = get_meeting_by_visio_code("911111111")
    assert meeting.name == "meeting"


def test_get_available_visio_code(client_app, authenticated_user):
    """Test that available visio code endpoint returns unique code."""
    response = client_app.get("/meeting/available-visio-code")
    available_code = response.json.get("available_visio_code")
    assert available_code
    assert not visio_code_exists(available_code)


def test_get_available_visio_code_no_user(client_app):
    """Test that unauthenticated user is redirected from visio code endpoint."""
    client_app.get("/meeting/available-visio-code", status=302)


def test_delegate_can_save_existing_delegated_meeting_not_running(
    client_app,
    authenticated_user,
    meeting_1_user_2,
    mock_meeting_is_not_running,
    caplog,
):
    """Test that existing meeting can be updated when not running."""
    assert db.session.scalar(db.select(db.func.count()).select_from(Meeting)) == 1

    res = client_app.get(f"/meeting/edit/{meeting_1_user_2.id}")
    res.forms[0]["name"] = "Mon meeting de test"
    res.forms[0]["welcome"] = "Bienvenue dans mon meeting de test"
    res.forms[0]["maxParticipants"] = 5
    res.forms[0]["duration"] = 60
    res.forms[0]["guestPolicy"] = "on"
    res.forms[0]["webcamsOnlyForModerator"] = "on"
    res.forms[0]["muteOnStart"] = "on"
    res.forms[0]["lockSettingsDisableCam"] = False
    res.forms[0]["lockSettingsDisableMic"] = False
    res.forms[0]["lockSettingsDisablePrivateChat"] = False
    res.forms[0]["lockSettingsDisablePublicChat"] = False
    res.forms[0]["lockSettingsDisableNote"] = False
    res.forms[0]["moderatorOnlyMessage"] = "Bienvenue aux modérateurs"
    res.forms[0]["logoutUrl"] = "https://log.out"
    res.forms[0]["moderatorPW"] = "Motdepasse1"
    res.forms[0]["attendeePW"] = "Motdepasse2"
    res.forms[0]["autoStartRecording"] = "on"
    res.forms[0]["allowStartStopRecording"] = "on"
    if client_app.app.config["ENABLE_PIN_MANAGEMENT"]:
        res.forms[0]["voiceBridge"] = "123456789"

    res = res.forms[0].submit()
    assert (
        "success",
        "delegated meeting modifications prises en compte",
    ) in res.flashes

    meetings = db.session.scalars(db.select(Meeting)).all()
    assert len(meetings) == 1
    meeting = meetings[0]

    assert meeting.owner_id == 2
    assert meeting.name == "delegated meeting"  # Name can not be edited
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
    if client_app.app.config["ENABLE_PIN_MANAGEMENT"]:
        assert meeting.voiceBridge == "123456789"
    data = "{'welcome': 'Bienvenue dans mon meeting de test', 'maxParticipants': 5, 'duration': 60, 'moderatorOnlyMessage': 'Bienvenue aux modérateurs', 'logoutUrl': 'https://log.out', 'moderatorPW': 'Motdepasse1', 'attendeePW': 'Motdepasse2', 'voiceBridge': '123456789'}"
    assert (
        f"Meeting delegated meeting {meeting.id} was updated by alice@domain.tld. Updated fields : {data}\n"
        in caplog.text
    )


def test_delete_recordings_failure_when_delete_meeting(
    mocker, client_app, authenticated_user, meeting
):
    """Test delete_all_recordings fails ."""
    mocker.patch(
        "b3desk.models.bbb.BBB.delete_all_recordings",
        return_value={"returncode": "FAILED", "message": "some error"},
    )
    res = client_app.post("/meeting/delete", {"id": meeting.id})
    assert (
        "error",
        "Impossible de supprimer les vidéos de ce séminaire : some error",
    ) in res.flashes


def test_create_meeting_ai_summary_requires_recording(
    client_app, meeting, authenticated_user
):
    res = client_app.get("/meeting/new")
    res.forms[0]["name"] = "Mon meeting de test"
    res.forms[0]["allowStartStopRecording"] = False
    res.forms[0]["ai_summary"] = "on"
    res = res.forms[0].submit()
    res.mustcontain(
        "La génération de résumé nécessite d'activer l'enregistrement manuel ou automatique."
    )


def test_get_meeting_secret_key_for_quick_meeting(client_app):
    """get_meeting_secret_key must compute the hash directly for quick meetings."""
    quick_meeting = get_quick_meeting_from_meeting_id()
    assert get_meeting_secret_key(
        quick_meeting, Role.moderator
    ) == get_quick_meeting_secret_key(quick_meeting, Role.moderator)


def test_get_role_for_quick_meeting_attendee(client_app):
    """get_role must resolve the attendee secret key of a quick meeting."""
    quick_meeting = get_quick_meeting_from_meeting_id()
    attendee_secret_key = get_quick_meeting_secret_key(quick_meeting, Role.attendee)
    assert get_role(quick_meeting, attendee_secret_key) == Role.attendee


def test_get_role_for_quick_meeting_authenticated(client_app):
    """get_role must resolve the authenticated secret key of a quick meeting."""
    quick_meeting = get_quick_meeting_from_meeting_id()
    authenticated_secret_key = get_quick_meeting_secret_key(
        quick_meeting, Role.authenticated
    )
    assert get_role(quick_meeting, authenticated_secret_key) == Role.authenticated


def test_get_role_for_quick_meeting_invalid_secret_key(client_app):
    """get_role must return None for a secret key matching no role of a quick meeting."""
    quick_meeting = get_quick_meeting_from_meeting_id()
    assert get_role(quick_meeting, "invalid-secret-key") is None


def test_url_for_role_returns_none_without_secret_key(client_app, meeting):
    """url_for_role must return None if no MeetingSecretKey row exists for the role."""
    db.session.execute(
        db.delete(MeetingSecretKey).where(
            MeetingSecretKey.meeting_id == meeting.id,
            MeetingSecretKey.role == Role.attendee.name,
        )
    )
    db.session.commit()

    assert meeting.url_for_role(Role.attendee) is None


def test_create_meeting_route(client_app, authenticated_user, meeting, bbb_response):
    """The create_meeting route must create the BBB room and redirect to welcome."""
    response = client_app.get(f"/meeting/create/{meeting.id}", status=302)

    assert bbb_response.called
    assert response.location == url_for("public.welcome")


def test_delete_old_meetings(
    app,
    client_app,
    time_machine,
    meeting_1_user_2,
    user,
    user_2,
    bbb_getRecordings_response,
):
    """Test that old shadow meetings are deleted."""
    meeting_1_user_2.last_connection_utc_datetime = datetime.datetime(2024, 1, 1)
    meeting_1_user_2.created_at = datetime.datetime(2024, 1, 1)

    db.session.commit()

    time_machine.move_to(datetime.datetime(2025, 6, 1))
    delete_old_meetings()
    voiceBridges = get_all_previous_voiceBridges()

    assert voiceBridges == ["222222222"]
    assert user.meetings == []


def test_delete_old_meetings_but_not_recent_meetings(
    app,
    client_app,
    time_machine,
    meeting,
    meeting_2,
    user,
    bbb_getRecordings_response,
):
    """Test that old shadow meetings are deleted except the most recent one."""
    meeting.last_connection_utc_datetime = datetime.datetime(2025, 1, 1)
    meeting.created_at = datetime.datetime(2024, 1, 1)
    meeting_2.last_connection_utc_datetime = datetime.datetime(2024, 1, 1)
    meeting_2.created_at = datetime.datetime(2024, 1, 1)
    db.session.commit()
    meeting_2_voicebridge = meeting_2.voiceBridge
    time_machine.move_to(datetime.datetime(2025, 6, 1))
    delete_old_meetings()
    voiceBridges = get_all_previous_voiceBridges()

    assert voiceBridges == [meeting_2_voicebridge]
    assert user.meetings == [meeting]


def test_delete_old_meetings_never_used_but_not_recent_meetings(
    app,
    client_app,
    time_machine,
    meeting,
    meeting_2,
    user,
    bbb_getRecordings_response,
):
    """Test that old shadow meetings never used are deleted except the most recent one."""
    meeting.last_connection_utc_datetime = None
    meeting.created_at = datetime.datetime(2025, 1, 1)
    meeting_2.last_connection_utc_datetime = None
    meeting_2.created_at = datetime.datetime(2024, 1, 1)
    db.session.commit()
    meeting_2_voicebridge = meeting_2.voiceBridge
    time_machine.move_to(datetime.datetime(2025, 6, 1))
    delete_old_meetings()
    voiceBridges = get_all_previous_voiceBridges()

    assert voiceBridges == [meeting_2_voicebridge]
    assert user.meetings == [meeting]


def test_inform_owner_before_meeting_deletion(
    app,
    client_app,
    time_machine,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    user,
    smtpd,
):
    """Test owner's meeting receveive a mail before meeting deletion."""
    assert len(smtpd.messages) == 0
    test_date = datetime.datetime(2024, 1, 1)
    third_mail_date = (
        test_date
        - datetime.timedelta(
            days=client_app.app.config["INACTIVITY_TIMER_CLEANUP_MEETING"]
        )
        + datetime.timedelta(days=DELAY_FOR_THIRD_EMAIL)
    )
    second_mail_date = (
        test_date
        - datetime.timedelta(
            days=client_app.app.config["INACTIVITY_TIMER_CLEANUP_MEETING"]
        )
        + datetime.timedelta(days=DELAY_FOR_SECOND_EMAIL)
    )
    first_mail_date = (
        test_date
        - datetime.timedelta(
            days=client_app.app.config["INACTIVITY_TIMER_CLEANUP_MEETING"]
        )
        + datetime.timedelta(days=DELAY_FOR_FIRST_EMAIL)
    )

    meeting.last_connection_utc_datetime = third_mail_date
    meeting.created_at = third_mail_date
    meeting_2.last_connection_utc_datetime = second_mail_date
    meeting_2.created_at = second_mail_date
    meeting_3.last_connection_utc_datetime = first_mail_date
    meeting_3.created_at = first_mail_date
    shadow_meeting.last_connection_utc_datetime = first_mail_date
    shadow_meeting.created_at = first_mail_date
    db.session.commit()

    time_machine.move_to(test_date)
    inform_owner_before_meeting_deletion()
    meetings_to_inform = get_inactive_meetings_to_inform()
    assert meetings_to_inform == [
        (meeting_3, DELAY_FOR_FIRST_EMAIL),
        (meeting_2, DELAY_FOR_SECOND_EMAIL),
        (meeting, DELAY_FOR_THIRD_EMAIL),
    ]
    assert len(smtpd.messages) == 3


def test_inform_owner_before_meeting_deletion_for_unused_meetings(
    app,
    client_app,
    time_machine,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    user,
    smtpd,
):
    """Test owner's meeting receveive a mail before meeting deletion."""
    assert len(smtpd.messages) == 0
    test_date = datetime.datetime(2024, 1, 1)
    third_mail_date = (
        test_date
        - datetime.timedelta(
            days=client_app.app.config["INACTIVITY_TIMER_CLEANUP_MEETING"]
        )
        + datetime.timedelta(days=DELAY_FOR_THIRD_EMAIL)
    )
    second_mail_date = (
        test_date
        - datetime.timedelta(
            days=client_app.app.config["INACTIVITY_TIMER_CLEANUP_MEETING"]
        )
        + datetime.timedelta(days=DELAY_FOR_SECOND_EMAIL)
    )
    first_mail_date = (
        test_date
        - datetime.timedelta(
            days=client_app.app.config["INACTIVITY_TIMER_CLEANUP_MEETING"]
        )
        + datetime.timedelta(days=DELAY_FOR_FIRST_EMAIL)
    )

    meeting.last_connection_utc_datetime = None
    meeting.created_at = third_mail_date
    meeting_2.last_connection_utc_datetime = None
    meeting_2.created_at = second_mail_date
    meeting_3.last_connection_utc_datetime = None
    meeting_3.created_at = first_mail_date
    shadow_meeting.last_connection_utc_datetime = None
    shadow_meeting.created_at = first_mail_date
    db.session.commit()

    time_machine.move_to(test_date)
    inform_owner_before_meeting_deletion()
    meetings_to_inform = get_inactive_meetings_to_inform()
    assert meetings_to_inform == [
        (meeting_3, DELAY_FOR_FIRST_EMAIL),
        (meeting_2, DELAY_FOR_SECOND_EMAIL),
        (meeting, DELAY_FOR_THIRD_EMAIL),
    ]
    assert len(smtpd.messages) == 3


def test_delete_old_meetings_no_action(app, client_app, caplog):
    """Test the cron task logs when there is no meeting to delete."""
    delete_old_meetings()
    assert "Celery cron task: no action required" in caplog.text


def test_inform_owner_before_meeting_deletion_no_action(app, client_app, caplog):
    """Test the cron task logs when there is no meeting to inform."""
    inform_owner_before_meeting_deletion()
    assert "Celery cron task: no action required" in caplog.text

import pytest
from joserfc import jwt
from joserfc.jwk import OctKey

BBB_SECRET = "test-bbb-secret"
RECORDING_URL = "https://bbb.test/playback/presentation/2.0/playback.html?meetingId=xyz"
RECORD_ID = "ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124"


def make_signed_parameters(payload, secret=BBB_SECRET):
    key = OctKey.import_key(secret.encode())
    return jwt.encode({"alg": "HS256"}, payload, key)


@pytest.fixture(autouse=True)
def bbb_secret(app):
    app.config["BIGBLUEBUTTON_SECRET"] = BBB_SECRET


@pytest.fixture
def bbb_recording(mocker):
    return mocker.patch(
        "b3desk.models.bbb.BBB.get_recordings",
        return_value=[{"playbacks": {"presentation": {"url": RECORDING_URL}}}],
    )


def test_valid_callback_returns_200_and_sends_email(
    client_app, meeting, smtpd, bbb_recording
):
    """Valid callback sends a notification email to the meeting owner and returns 200."""
    signed = make_signed_parameters(
        {"meeting_id": meeting.meetingID, "record_id": RECORD_ID}
    )

    assert len(smtpd.messages) == 0
    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=200,
    )
    assert len(smtpd.messages) == 1


def test_invalid_signature_returns_401(client_app, meeting, smtpd):
    """JWT signed with wrong secret returns 401, no email sent."""
    signed = make_signed_parameters(
        {"meeting_id": meeting.meetingID, "record_id": RECORD_ID},
        secret="wrong-secret",
    )

    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=401,
    )
    assert len(smtpd.messages) == 0


def test_unknown_meeting_returns_410(client_app, smtpd):
    """Callback for a meeting absent from the database returns 410, no email sent."""
    signed = make_signed_parameters(
        {
            "meeting_id": "meeting-persistent-9999--hash",
            "record_id": RECORD_ID,
        }
    )

    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=410,
    )
    assert len(smtpd.messages) == 0


def test_invalid_meeting_id_returns_410(client_app, meeting, smtpd, bbb_recording):
    """Valid callback sends a notification email to the meeting owner and returns 200."""
    signed = make_signed_parameters(
        {"meeting_id": str(meeting.id), "record_id": RECORD_ID}
    )

    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=410,
    )
    assert len(smtpd.messages) == 0


def test_recording_not_found_returns_500(client_app, meeting, smtpd, mocker):
    """When BBB returns no recordings, returns 500 without sending email."""
    mocker.patch("b3desk.models.bbb.BBB.get_recordings", return_value=[])

    signed = make_signed_parameters(
        {"meeting_id": meeting.meetingID, "record_id": RECORD_ID}
    )

    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=500,
    )
    assert len(smtpd.messages) == 0

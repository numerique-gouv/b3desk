from joserfc import jwt
from joserfc.jwk import OctKey

RECORD_ID = "ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124"


def test_valid_callback_returns_200_and_sends_email(
    client_app, meeting, smtpd, bbb_recording, make_signed_parameters
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
    key = OctKey.import_key(b"wrong-secret")
    signed = jwt.encode(
        {"alg": "HS256"}, {"meeting_id": meeting.meetingID, "record_id": RECORD_ID}, key
    )

    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=401,
    )
    assert len(smtpd.messages) == 0


def test_unknown_meeting_returns_410(client_app, smtpd, make_signed_parameters):
    """Callback for a meeting absent from the database returns 410, no email sent."""
    signed = make_signed_parameters(
        {"meeting_id": "meeting-persistent-9999--hash", "record_id": RECORD_ID}
    )

    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=410,
    )
    assert len(smtpd.messages) == 0


def test_invalid_meeting_id_returns_410(
    client_app, meeting, smtpd, bbb_recording, make_signed_parameters
):
    """Callback for a meeting with invalid structure id from bbb returns 410, no email sent."""
    signed = make_signed_parameters(
        {"meeting_id": str(meeting.id), "record_id": RECORD_ID}
    )

    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=410,
    )
    assert len(smtpd.messages) == 0


def test_recording_not_found_returns_500(
    client_app, meeting, smtpd, mocker, make_signed_parameters
):
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

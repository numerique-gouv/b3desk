import datetime
import json

import requests
from b3desk import cache
from b3desk.models import db
from b3desk.models.meetings import MeetingSession
from b3desk.tasks import recording_scheduled_key
from joserfc import jwt
from joserfc.jwk import OctKey

RECORD_ID = "ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124"


def test_valid_callback_returns_200_and_sends_email(
    client_app, meeting, smtpd, bbb_recording, make_signed_parameters
):
    """Valid callback sends a notification email to the meeting owner and returns 200."""
    signed = make_signed_parameters(
        {"meeting_id": meeting.bbb_meeting_id, "record_id": RECORD_ID}
    )

    assert len(smtpd.messages) == 0
    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=200,
    )
    assert len(smtpd.messages) == 1
    sent = smtpd.messages[0]
    assert meeting.owner.email in sent["To"]
    parts = {part.get_content_type(): part for part in sent.walk()}
    assert "text/plain" in parts
    assert "text/html" in parts
    html_body = parts["text/html"].get_payload(decode=True).decode()
    text_body = parts["text/plain"].get_payload(decode=True).decode()
    assert "https://bbb.test/playback/presentation" in html_body
    assert "https://bbb.test/playback/presentation" in text_body


def test_invalid_signature_returns_401(client_app, meeting, smtpd):
    """JWT signed with wrong secret returns 401, no email sent."""
    key = OctKey.import_key(b"wrong-secret")
    signed = jwt.encode(
        {"alg": "HS256"},
        {"meeting_id": meeting.bbb_meeting_id, "record_id": RECORD_ID},
        key,
    )

    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=401,
    )
    assert len(smtpd.messages) == 0


def test_missing_signed_parameters_returns_410(client_app, smtpd):
    """POST without signed_parameters returns 410 to stop BBB retries."""
    client_app.post("/bbb-callback/recording_status", {}, status=410)
    assert len(smtpd.messages) == 0


def test_missing_meeting_id_claim_returns_410(
    client_app, smtpd, make_signed_parameters
):
    """Token missing the meeting_id claim returns 410 to stop BBB retries."""
    signed = make_signed_parameters({"record_id": RECORD_ID})
    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=410,
    )
    assert len(smtpd.messages) == 0


def test_missing_record_id_claim_returns_410(
    client_app, meeting, smtpd, make_signed_parameters
):
    """Token missing the record_id claim returns 410 to stop BBB retries."""
    signed = make_signed_parameters({"meeting_id": meeting.bbb_meeting_id})
    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=410,
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


def test_non_digit_meeting_id_returns_410(client_app, smtpd, make_signed_parameters):
    """BBB-shaped meeting_id with non-digit id segment returns 410."""
    signed = make_signed_parameters(
        {"meeting_id": "meeting-persistent-abc--hash", "record_id": RECORD_ID}
    )

    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=410,
    )
    assert len(smtpd.messages) == 0


def test_duplicate_callback_for_same_record_id_only_sends_one_mail(
    client_app, meeting, smtpd, bbb_recording, make_signed_parameters
):
    """A second callback for the same record_id is acknowledged but does not re-notify."""
    signed = make_signed_parameters(
        {"meeting_id": meeting.bbb_meeting_id, "record_id": RECORD_ID}
    )

    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=200,
    )
    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=200,
    )
    assert len(smtpd.messages) == 1


def test_callback_acknowledges_even_when_bbb_has_no_recording_yet(
    client_app, meeting, smtpd, mocker, make_signed_parameters
):
    """Recording lookup happens in the task; the callback always acknowledges."""
    from b3desk.models.bbb import BBB

    mocker.patch.object(BBB.get_recordings, "uncached", return_value=[])

    signed = make_signed_parameters(
        {"meeting_id": meeting.bbb_meeting_id, "record_id": RECORD_ID}
    )

    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=200,
    )
    assert len(smtpd.messages) == 0


def test_second_format_callback_does_not_leak_recording_to_earlier_session(
    client_app, meeting, bbb_recording, make_signed_parameters
):
    """A later callback for the same recording (e.g. a second format) must not reassign the recording to an earlier, unrecorded session."""
    earlier_session = MeetingSession(
        meeting_id=meeting.id,
        started_at=datetime.datetime(2023, 1, 1, 10, 0, 0),
        ended_at=datetime.datetime(2023, 1, 1, 10, 30, 0),
    )
    later_session = MeetingSession(
        meeting_id=meeting.id,
        started_at=datetime.datetime(2023, 1, 1, 11, 0, 0),
        ended_at=datetime.datetime(2023, 1, 1, 11, 30, 0),
    )
    db.session.add_all([earlier_session, later_session])
    db.session.commit()

    signed = make_signed_parameters(
        {"meeting_id": meeting.bbb_meeting_id, "record_id": RECORD_ID}
    )

    # First callback (e.g. presentation format) matches the most recent
    # session that has no recording yet.
    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=200,
    )
    # A second callback for the same recording (e.g. video/ai-summary format)
    # must be a no-op regarding session matching, not fall back to the older
    # session that never had a recording.
    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=200,
    )

    db.session.refresh(earlier_session)
    db.session.refresh(later_session)
    assert later_session.recording_id == RECORD_ID
    assert earlier_session.recording_id is None


def test_subsequent_callback_triggers_recheck(
    client_app, meeting, mocker, make_signed_parameters
):
    """A callback arriving after scheduling triggers an immediate re-check task."""
    cache.set(recording_scheduled_key(RECORD_ID), True)
    delay = mocker.patch(
        "b3desk.endpoints.bbb_callback.send_recording_notification.delay"
    )

    signed = make_signed_parameters(
        {"meeting_id": meeting.bbb_meeting_id, "record_id": RECORD_ID}
    )
    client_app.post(
        "/bbb-callback/recording_status",
        {"signed_parameters": signed},
        status=200,
    )
    delay.assert_called_once_with(meeting.id, RECORD_ID)


def test_analytics_callback_relays_payload_to_configured_url(
    client_app, mocker, make_analytics_bearer_token
):
    """A valid callback is relayed as-is to the configured analytics service."""
    signed = make_analytics_bearer_token({})
    mock_post = mocker.patch("b3desk.endpoints.bbb_callback.requests.post")

    payload = {"meeting_id": "some-external-id", "data": {"foo": "bar"}}
    client_app.post_json(
        "/bbb-callback/analytics",
        payload,
        headers={"Authorization": f"Bearer {signed}"},
        status=200,
    )

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == client_app.app.config["BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL"]
    assert json.loads(kwargs["data"]) == payload
    assert kwargs["headers"]["Authorization"] == f"Bearer {signed}"


def test_analytics_callback_still_acknowledges_when_relay_fails(
    client_app, meeting, mocker, make_analytics_bearer_token
):
    """A relay failure is retried, then logged, without failing the callback.

    BBB retries non-2xx/410 responses, and the relay target is a third party
    outside our control: its failure must not cause BBB to retry, nor discard
    the session update we already made from BBB's own payload.
    """
    session = MeetingSession(meeting_id=meeting.id)
    db.session.add(session)
    db.session.commit()

    signed = make_analytics_bearer_token({})
    mock_post = mocker.patch(
        "b3desk.endpoints.bbb_callback.requests.post",
        side_effect=requests.RequestException("boom"),
    )

    before = datetime.datetime.now()
    client_app.post_json(
        "/bbb-callback/analytics",
        {
            "meeting_id": meeting.bbb_meeting_id,
            "data": {"attendees": [{"ext_user_id": "w_1", "name": "Alice"}]},
        },
        headers={"Authorization": f"Bearer {signed}"},
        status=200,
    )
    after = datetime.datetime.now()

    assert mock_post.call_count == 3
    db.session.refresh(session)
    assert before <= session.ended_at <= after
    assert session.participant_count == 1


def test_analytics_callback_invalid_signature_returns_401(client_app, mocker):
    """JWT signed with the wrong secret returns 401, nothing is relayed."""
    key = OctKey.import_key(b"wrong-secret")
    signed = jwt.encode({"alg": "HS512"}, {}, key, algorithms=["HS512"])
    mock_post = mocker.patch("b3desk.endpoints.bbb_callback.requests.post")

    client_app.post_json(
        "/bbb-callback/analytics",
        {},
        headers={"Authorization": f"Bearer {signed}"},
        status=401,
    )
    mock_post.assert_not_called()


def test_analytics_callback_wrong_algorithm_returns_401(
    client_app, mocker, make_signed_parameters
):
    """A token with the right secret but the wrong algorithm is rejected.

    Regression test: BBB signs this specific callback with HS512, unlike its
    other callbacks (HS256). A token correctly signed with the shared secret
    but using HS256 must still be rejected rather than silently crashing
    (joserfc raises ``UnsupportedAlgorithmError`` for algorithms outside its
    default allowlist unless explicitly requested).
    """
    signed = make_signed_parameters({})
    mock_post = mocker.patch("b3desk.endpoints.bbb_callback.requests.post")

    client_app.post_json(
        "/bbb-callback/analytics",
        {},
        headers={"Authorization": f"Bearer {signed}"},
        status=401,
    )
    mock_post.assert_not_called()


def test_analytics_callback_missing_token_returns_401(client_app, mocker):
    """Missing Authorization header returns 401, nothing is relayed."""
    mock_post = mocker.patch("b3desk.endpoints.bbb_callback.requests.post")

    client_app.post_json("/bbb-callback/analytics", {}, status=401)
    mock_post.assert_not_called()


def test_analytics_callback_without_configured_url_is_not_relayed(
    client_app, mocker, make_analytics_bearer_token
):
    """When no external analytics URL is configured, the callback is a no-op."""
    signed = make_analytics_bearer_token({})
    mock_post = mocker.patch("b3desk.endpoints.bbb_callback.requests.post")
    client_app.app.config["BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL"] = None

    client_app.post_json(
        "/bbb-callback/analytics",
        {"foo": "bar"},
        headers={"Authorization": f"Bearer {signed}"},
        status=200,
    )
    mock_post.assert_not_called()


def test_analytics_callback_falls_back_to_now_when_finish_is_missing(
    client_app, meeting, mocker, make_analytics_bearer_token
):
    """Missing/unparseable finish timestamp still closes the session, using 'now'."""
    session = MeetingSession(meeting_id=meeting.id)
    db.session.add(session)
    db.session.commit()

    signed = make_analytics_bearer_token({})
    mocker.patch("b3desk.endpoints.bbb_callback.requests.post")

    before = datetime.datetime.now()
    client_app.post_json(
        "/bbb-callback/analytics",
        {"meeting_id": meeting.bbb_meeting_id, "data": {}},
        headers={"Authorization": f"Bearer {signed}"},
        status=200,
    )
    after = datetime.datetime.now()

    db.session.refresh(session)
    assert session.ended_at is not None
    assert before <= session.ended_at <= after
    assert session.participant_count is None


def test_analytics_callback_ignores_non_string_timestamps(
    client_app, meeting, mocker, make_analytics_bearer_token
):
    """Non-string start/finish values (malformed payload) don't crash the callback.

    Regression test: ``datetime.fromisoformat`` raises ``TypeError`` (not
    ``ValueError``) for non-string input, e.g. if BBB ever sends a number or
    object instead of an ISO-8601 string.
    """
    session = MeetingSession(meeting_id=meeting.id)
    db.session.add(session)
    db.session.commit()

    signed = make_analytics_bearer_token({})
    mocker.patch("b3desk.endpoints.bbb_callback.requests.post")

    before = datetime.datetime.now()
    client_app.post_json(
        "/bbb-callback/analytics",
        {
            "meeting_id": meeting.bbb_meeting_id,
            "data": {"start": 12345, "finish": {"not": "a string"}},
        },
        headers={"Authorization": f"Bearer {signed}"},
        status=200,
    )
    after = datetime.datetime.now()

    db.session.refresh(session)
    assert before <= session.ended_at <= after


def test_analytics_callback_without_open_session_is_still_acknowledged(
    client_app, meeting, mocker, make_analytics_bearer_token
):
    """No open session for the meeting: callback is acknowledged, nothing to update."""
    signed = make_analytics_bearer_token({})
    mocker.patch("b3desk.endpoints.bbb_callback.requests.post")

    client_app.post_json(
        "/bbb-callback/analytics",
        {"meeting_id": meeting.bbb_meeting_id, "data": {}},
        headers={"Authorization": f"Bearer {signed}"},
        status=200,
    )
    assert MeetingSession.query.filter_by(meeting_id=meeting.id).count() == 0


def test_analytics_callback_stores_session_attendees(
    client_app, meeting, mocker, make_analytics_bearer_token
):
    """Attendees details are stored, keeping the first join and the last leave."""
    session = MeetingSession(meeting_id=meeting.id)
    db.session.add(session)
    db.session.commit()

    signed = make_analytics_bearer_token({})
    mocker.patch("b3desk.endpoints.bbb_callback.requests.post")

    client_app.post_json(
        "/bbb-callback/analytics",
        {
            "meeting_id": meeting.bbb_meeting_id,
            "data": {
                "attendees": [
                    {
                        "ext_user_id": "w_1",
                        "name": "Alice",
                        "moderator": True,
                        "joins": ["2026-09-23T10:00:00+00:00"],
                        "leaves": ["2026-09-23T11:00:00+00:00"],
                        "duration": 3600,
                    },
                    {
                        "ext_user_id": "w_2",
                        "name": "Bob",
                        "moderator": False,
                        "joins": [
                            "2026-09-23T10:30:00+00:00",
                            "2026-09-23T10:10:00+00:00",
                        ],
                        "leaves": [
                            "2026-09-23T10:20:00+00:00",
                            "2026-09-23T10:50:00+00:00",
                        ],
                        "duration": 1800,
                    },
                    {"ext_user_id": "w_3", "name": "Charlie", "joins": "invalid"},
                ]
            },
        },
        headers={"Authorization": f"Bearer {signed}"},
        status=200,
    )

    def local(value):
        return datetime.datetime.fromisoformat(value).astimezone().replace(tzinfo=None)

    db.session.refresh(session)
    assert session.participant_count == 3
    attendees = {attendee.name: attendee for attendee in session.attendees}
    assert attendees.keys() == {"Alice", "Bob", "Charlie"}

    assert attendees["Alice"].moderator is True
    assert attendees["Alice"].joins == local("2026-09-23T10:00:00+00:00")
    assert attendees["Alice"].leaves == local("2026-09-23T11:00:00+00:00")
    assert attendees["Alice"].duration == 3600

    assert attendees["Bob"].moderator is False
    assert attendees["Bob"].joins == local("2026-09-23T10:10:00+00:00")
    assert attendees["Bob"].leaves == local("2026-09-23T10:50:00+00:00")
    assert attendees["Bob"].duration == 1800

    assert attendees["Charlie"].moderator is False
    assert attendees["Charlie"].joins is None
    assert attendees["Charlie"].leaves is None
    assert attendees["Charlie"].duration is None

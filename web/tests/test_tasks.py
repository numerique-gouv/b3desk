import datetime

from b3desk import cache
from b3desk.tasks import recording_min_reached_key
from b3desk.tasks import recording_notified_key
from b3desk.tasks import send_recording_notification

RECORD_ID = "ffbfc4cc24428694e8b53a4e144f414052431693-1530718721124"


def _mock_recording(mocker, playbacks):
    # BBB cannot be imported at module level: b3desk.models.bbb reads
    # current_app at import time, which needs an active app context.
    from b3desk.models.bbb import BBB

    return mocker.patch.object(
        BBB.get_recordings,
        "uncached",
        return_value=[
            {
                "playbacks": playbacks,
                "start_date": datetime.datetime(
                    2026, 1, 1, tzinfo=datetime.timezone.utc
                ),
                "name": "x",
            }
        ],
    )


def test_meeting_deleted(client_app, smtpd):
    """If the meeting is deleted before the task runs, skip mailing silently."""
    send_recording_notification(
        meeting_id="99999", bbb_recording_id="unknown", is_min_deadline=True
    )
    assert len(smtpd.messages) == 0


def test_no_recording(client_app, meeting, smtpd, mocker):
    """If BBB returns no recording at task time, skip silently."""
    from b3desk.models.bbb import BBB

    mocker.patch.object(BBB.get_recordings, "uncached", return_value=[])
    send_recording_notification(
        meeting_id=meeting.id, bbb_recording_id="unknown", is_min_deadline=True
    )
    assert len(smtpd.messages) == 0


def test_unexpected_structure(client_app, meeting, smtpd, mocker):
    """If BBB returns a recording with an unexpected shape, skip silently."""
    from b3desk.models.bbb import BBB

    mocker.patch.object(
        BBB.get_recordings, "uncached", return_value=[{"unexpected": "shape"}]
    )
    send_recording_notification(
        meeting_id=meeting.id, bbb_recording_id="unknown", is_min_deadline=True
    )
    assert len(smtpd.messages) == 0


def test_incomplete_formats_not_sent_at_min_delay(client_app, meeting, smtpd, mocker):
    """At the min delay, an incomplete recording does not trigger a mail."""
    _mock_recording(mocker, playbacks={})
    send_recording_notification(
        meeting_id=meeting.id, bbb_recording_id=RECORD_ID, is_min_deadline=True
    )
    assert len(smtpd.messages) == 0


def test_not_sent_before_min_delay_even_when_complete(
    client_app, meeting, smtpd, mocker
):
    """A complete recording is not mailed until the minimum delay has elapsed."""
    _mock_recording(
        mocker,
        playbacks={"presentation": {"url": "https://bbb.test/playback/presentation"}},
    )
    send_recording_notification(meeting_id=meeting.id, bbb_recording_id=RECORD_ID)
    assert len(smtpd.messages) == 0


def test_sent_at_min_delay_when_complete(client_app, meeting, smtpd, mocker):
    """The min-delay task sends as soon as all expected formats are present."""
    _mock_recording(
        mocker,
        playbacks={"presentation": {"url": "https://bbb.test/playback/presentation"}},
    )
    send_recording_notification(
        meeting_id=meeting.id, bbb_recording_id=RECORD_ID, is_min_deadline=True
    )
    assert len(smtpd.messages) == 1


def test_sent_after_min_delay_flag_when_complete(client_app, meeting, smtpd, mocker):
    """Once the min delay has elapsed, a later callback sends when complete."""
    cache.set(recording_min_reached_key(RECORD_ID), True)
    _mock_recording(
        mocker,
        playbacks={"presentation": {"url": "https://bbb.test/playback/presentation"}},
    )
    send_recording_notification(meeting_id=meeting.id, bbb_recording_id=RECORD_ID)
    assert len(smtpd.messages) == 1


def test_lists_all_available_formats(client_app, meeting, smtpd, mocker, caplog):
    """Both presentation and video formats appear in the notification mail, and a success log is emitted."""
    _mock_recording(
        mocker,
        playbacks={
            "presentation": {"url": "https://bbb.test/playback/presentation"},
            "video": {
                "url": "https://bbb.test/playback/video/",
                "direct_link": "https://bbb.test/playback/video/video-0.m4v",
            },
        },
    )
    send_recording_notification(
        meeting_id=meeting.id, bbb_recording_id=RECORD_ID, is_min_deadline=True
    )
    assert len(smtpd.messages) == 1
    sent = smtpd.messages[0]
    parts = {part.get_content_type(): part for part in sent.walk()}
    html_body = parts["text/html"].get_payload(decode=True).decode()
    assert "https://bbb.test/playback/presentation" in html_body
    assert "https://bbb.test/playback/video/video-0.m4v" in html_body
    assert f"Email sent to {meeting.owner.email}" in caplog.text


def test_ai_summary_expected_but_absent_waits(client_app, meeting, smtpd, mocker):
    """When the AI summary is expected but not yet rendered, no mail at min delay."""
    meeting.ai_summary = True
    _mock_recording(
        mocker,
        playbacks={"presentation": {"url": "https://bbb.test/playback/presentation"}},
    )
    send_recording_notification(
        meeting_id=meeting.id, bbb_recording_id=RECORD_ID, is_min_deadline=True
    )
    assert len(smtpd.messages) == 0


def test_ai_summary_expected_and_present_sends(client_app, meeting, smtpd, mocker):
    """When the AI summary is expected and present, the mail is sent."""
    meeting.ai_summary = True
    _mock_recording(
        mocker,
        playbacks={
            "presentation": {"url": "https://bbb.test/playback/presentation"},
            "ai-summary": {"url": "https://bbb.test/playback/ai-summary.html"},
        },
    )
    send_recording_notification(
        meeting_id=meeting.id, bbb_recording_id=RECORD_ID, is_min_deadline=True
    )
    assert len(smtpd.messages) == 1


def test_max_delay_sends_incomplete_recording(client_app, meeting, smtpd, mocker):
    """The max-delay safety net mails the available formats even when incomplete."""
    meeting.ai_summary = True
    _mock_recording(
        mocker,
        playbacks={"presentation": {"url": "https://bbb.test/playback/presentation"}},
    )
    send_recording_notification(
        meeting_id=meeting.id, bbb_recording_id=RECORD_ID, force=True
    )
    assert len(smtpd.messages) == 1


def test_not_resent_once_notified(client_app, meeting, smtpd, mocker):
    """A recording already notified is never mailed again."""
    cache.set(recording_notified_key(RECORD_ID), True)
    _mock_recording(
        mocker,
        playbacks={"presentation": {"url": "https://bbb.test/playback/presentation"}},
    )
    send_recording_notification(
        meeting_id=meeting.id, bbb_recording_id=RECORD_ID, force=True
    )
    assert len(smtpd.messages) == 0


def test_concurrent_claim_prevents_duplicate_mail(client_app, meeting, smtpd, mocker):
    """If another worker claims the notification between check and send, skip."""
    _mock_recording(
        mocker,
        playbacks={"presentation": {"url": "https://bbb.test/playback/presentation"}},
    )
    mocker.patch("b3desk.tasks.cache.add", return_value=False)
    send_recording_notification(
        meeting_id=meeting.id, bbb_recording_id=RECORD_ID, force=True
    )
    assert len(smtpd.messages) == 0

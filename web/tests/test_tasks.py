from b3desk.tasks import send_recording_notification


def test_send_recording_notification_meeting_deleted(client_app, smtpd):
    """If the meeting is deleted before the task runs, skip mailing silently."""
    send_recording_notification(
        meeting_id=99999,
        recording_url="https://bbb.test/playback/presentation",
        recording_name="some recording",
        recording_start="2026-01-01T00:00:00+00:00",
    )
    assert len(smtpd.messages) == 0

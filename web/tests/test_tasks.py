from b3desk.tasks import send_recording_notification


def test_send_recording_notification_meeting_deleted(client_app, smtpd):
    """If the meeting is deleted before the task runs, skip mailing silently."""
    send_recording_notification(meeting_id=99999, bbb_recording_id="unknown")
    assert len(smtpd.messages) == 0


def test_send_recording_notification_no_recording(client_app, meeting, smtpd, mocker):
    """If BBB returns no recording at task time, skip silently."""
    from b3desk.models.bbb import BBB

    mocker.patch.object(BBB.get_recordings, "uncached", return_value=[])
    send_recording_notification(meeting_id=meeting.id, bbb_recording_id="unknown")
    assert len(smtpd.messages) == 0


def test_send_recording_notification_unexpected_structure(
    client_app, meeting, smtpd, mocker
):
    """If BBB returns a recording with an unexpected shape, skip silently."""
    from b3desk.models.bbb import BBB

    mocker.patch.object(
        BBB.get_recordings, "uncached", return_value=[{"unexpected": "shape"}]
    )
    send_recording_notification(meeting_id=meeting.id, bbb_recording_id="unknown")
    assert len(smtpd.messages) == 0

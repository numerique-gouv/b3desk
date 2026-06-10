import datetime

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


def test_send_recording_notification_no_usable_format(
    client_app, meeting, smtpd, mocker
):
    """When BBB returns a recording without presentation or video, skip mailing."""
    from b3desk.models.bbb import BBB

    mocker.patch.object(
        BBB.get_recordings,
        "uncached",
        return_value=[
            {
                "playbacks": {},
                "start_date": datetime.datetime(
                    2026, 1, 1, tzinfo=datetime.timezone.utc
                ),
                "name": "x",
            }
        ],
    )
    send_recording_notification(meeting_id=meeting.id, bbb_recording_id="x")
    assert len(smtpd.messages) == 0


def test_send_recording_notification_lists_all_available_formats(
    client_app, meeting, smtpd, mocker
):
    """Both presentation and video formats appear in the notification mail."""
    from b3desk.models.bbb import BBB

    mocker.patch.object(
        BBB.get_recordings,
        "uncached",
        return_value=[
            {
                "playbacks": {
                    "presentation": {"url": "https://bbb.test/playback/presentation"},
                    "video": {
                        "url": "https://bbb.test/playback/video/",
                        "direct_link": "https://bbb.test/playback/video/video-0.m4v",
                    },
                },
                "start_date": datetime.datetime(
                    2026, 1, 1, tzinfo=datetime.timezone.utc
                ),
                "name": "x",
            }
        ],
    )
    send_recording_notification(meeting_id=meeting.id, bbb_recording_id="x")
    assert len(smtpd.messages) == 1
    sent = smtpd.messages[0]
    parts = {part.get_content_type(): part for part in sent.walk()}
    html_body = parts["text/html"].get_payload(decode=True).decode()
    assert "https://bbb.test/playback/presentation" in html_body
    assert "https://bbb.test/playback/video/video-0.m4v" in html_body

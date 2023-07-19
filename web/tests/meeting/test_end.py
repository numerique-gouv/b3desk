from flaskr.models import Meeting


def test_end_bbb_meeting(app, client_app, authenticated_user, meeting, mocker):
    meeting = Meeting.query.get(1)
    meeting_id = meeting.id
    mocked_end = mocker.patch("flaskr.models.BBB.end")

    response = client_app.post(
        "/meeting/end",
        {"meeting_id": meeting_id},
    )

    assert mocked_end.called
    assert response.status_code == 302
    assert "welcome" in response.location

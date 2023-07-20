def test_end_bbb_meeting(app, client_app, authenticated_user, meeting, mocker):
    mocked_end = mocker.patch("flaskr.models.BBB.end")

    response = client_app.post(
        "/meeting/end",
        {"meeting_id": meeting.id},
        status=302,
    )

    assert mocked_end.called
    assert "welcome" in response.location

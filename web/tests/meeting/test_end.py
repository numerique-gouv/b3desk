def test_end_bbb_meeting(client_app, authenticated_user, meeting, mocker):
    mocked_end = mocker.patch("b3desk.models.bbb.BBB.end")

    response = client_app.post(
        "/meeting/end",
        {"meeting_id": meeting.id},
        status=302,
    )

    assert mocked_end.called
    assert "welcome" in response.location

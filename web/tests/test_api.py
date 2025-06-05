import datetime


def test_api_meetings_nominal(
    client_app,
    user,
    meeting,
    meeting_2,
    meeting_3,
    shadow_meeting,
    iam_token,
):
    res = client_app.get(
        "/api/meetings", headers={"Authorization": f"Bearer {iam_token.access_token}"}
    )
    assert res.json["meetings"][0]["name"] == "meeting"
    assert res.json["meetings"][1]["name"] == "a meeting"
    assert res.json["meetings"][2]["name"] == "meeting"
    assert res.json["meetings"][0] == {
        "PIN": "111111111",
        "attendee_url": "http://localhost:5000/meeting/signin/invite/1/creator/1/hash/9120d7b37d540816e62bea4703bf0376b69297c5",
        "moderator_url": "http://localhost:5000/meeting/signin/moderateur/1/creator/1/hash/09aa80a2801e126893b2ce209df71cb7281561eb",
        "name": "meeting",
        "phone_number": "+33bbbphonenumber",
    }

    assert len(res.json["meetings"]) == 3

    client_app.app.config["ENABLE_PIN_MANAGEMENT"] = False
    res = client_app.get(
        "/api/meetings", headers={"Authorization": f"Bearer {iam_token.access_token}"}
    )

    assert res.json["meetings"][0] == {
        "attendee_url": "http://localhost:5000/meeting/signin/invite/1/creator/1/hash/9120d7b37d540816e62bea4703bf0376b69297c5",
        "moderator_url": "http://localhost:5000/meeting/signin/moderateur/1/creator/1/hash/09aa80a2801e126893b2ce209df71cb7281561eb",
        "name": "meeting",
    }

    assert len(res.json["meetings"]) == 3

    assert res.json["meetings"][1]["name"] == "a meeting"
    assert res.json["meetings"][2]["name"] == "meeting"
    assert len(res.json["meetings"]) == 3


def test_api_meetings_no_token(client_app):
    client_app.get("/api/meetings", status=401)


def test_api_meetings_invalid_token(client_app):
    client_app.get(
        "/api/meetings", headers={"Authorization": "Bearer invalid-token"}, status=403
    )


def test_api_meetings_token_expired(client_app, iam_server, iam_client, iam_user, user):
    iam_token = iam_server.random_token(
        client=iam_client,
        subject=iam_user,
        issue_date=datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc),
    )

    client_app.get(
        "/api/meetings",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
        status=403,
    )

    iam_token.delete()


def test_api_meetings_client_id_missing_in_token_audience(
    client_app, iam_server, iam_client, iam_user, user
):
    iam_token = iam_server.models.Token(
        client=iam_client,
        subject=iam_user,
        audience="some-other-audience",
    )

    client_app.get(
        "/api/meetings",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
        status=403,
    )

    iam_token.delete()


def test_api_meetings_missing_scope_in_token(
    client_app, iam_server, iam_client, iam_user, user
):
    iam_token = iam_server.models.Token(
        client=iam_client,
        subject=iam_user,
        scope=["openid"],
    )

    client_app.get(
        "/api/meetings",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
        status=403,
    )

    iam_token.delete()


def test_api_existing_shadow_meeting(
    client_app,
    user,
    shadow_meeting,
    shadow_meeting_2,
    shadow_meeting_3,
    meeting,
    iam_token,
):
    res = client_app.get(
        "/api/shadow-meeting",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
    )
    assert res.json["shadow-meeting"]
    assert res.json["shadow-meeting"][0]["name"] == "shadow meeting"
    assert (
        f"/meeting/signin/moderateur/{shadow_meeting.id}/creator/{user.id}/hash/"
        in res.json["shadow-meeting"][0]["moderator_url"]
    )
    assert (
        f"/meeting/signin/invite/{shadow_meeting.id}/creator/{user.id}/hash/"
        in res.json["shadow-meeting"][0]["attendee_url"]
    )
    assert len(res.json["shadow-meeting"]) == 1


def test_api_new_shadow_meeting(
    client_app,
    user,
    meeting,
    iam_token,
):
    res = client_app.get(
        "/api/shadow-meeting",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
    )
    assert res.json["shadow-meeting"]
    assert res.json["shadow-meeting"][0]["name"] == "le séminaire de Alice Cooper"
    assert (
        f"/meeting/signin/moderateur/2/creator/{user.id}/hash/"
        in res.json["shadow-meeting"][0]["moderator_url"]
    )
    assert (
        f"/meeting/signin/invite/2/creator/{user.id}/hash/"
        in res.json["shadow-meeting"][0]["attendee_url"]
    )
    assert len(res.json["shadow-meeting"]) == 1

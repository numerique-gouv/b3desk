import datetime


def test_api_meetings_nominal(client_app, user, meeting, iam_token):
    res = client_app.get(
        "/api/meetings", headers={"Authorization": f"Bearer {iam_token.access_token}"}
    )
    assert res.json["meetings"]
    assert res.json["meetings"][0]["name"] == "meeting"
    assert (
        f"/meeting/signin/{meeting.id}/creator/{user.id}/hash/"
        in res.json["meetings"][0]["moderator_url"]
    )
    assert (
        f"/meeting/signin/{meeting.id}/creator/{user.id}/hash/"
        in res.json["meetings"][0]["attendee_url"]
    )


def test_api_meetings_no_token(client_app):
    client_app.get("/api/meetings", status=401)


def test_api_meetings_invalid_token(client_app):
    client_app.get(
        "/api/meetings", headers={"Authorization": "Bearer invalid-token"}, status=403
    )


def test_api_meetings_token_expired(client_app, iam_server, iam_client, iam_user, user):
    iam_token = iam_server.models.Token(
        access_token="access_token_example",
        audience=iam_client,
        client=iam_client,
        id="token_id",
        issue_date=datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc),
        lifetime=36000,
        refresh_token="refresh_token_example",
        revokation_date=None,
        scope=["openid", "profile", "email"],
        subject=iam_user,
        token_id="token_id",
        type="access_token",
    )
    iam_token.save()

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
        access_token="access_token_example",
        audience="some-other-audience",
        client=iam_client,
        id="token_id",
        issue_date=datetime.datetime.now(tz=datetime.timezone.utc),
        lifetime=36000,
        refresh_token="refresh_token_example",
        revokation_date=None,
        scope=["openid", "profile", "email"],
        subject=iam_user,
        token_id="token_id",
        type="access_token",
    )
    iam_token.save()

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
        access_token="access_token_example",
        audience=iam_client,
        client=iam_client,
        id="token_id",
        issue_date=datetime.datetime.now(tz=datetime.timezone.utc),
        lifetime=36000,
        refresh_token="refresh_token_example",
        revokation_date=None,
        scope=["openid"],
        subject=iam_user,
        token_id="token_id",
        type="access_token",
    )
    iam_token.save()

    client_app.get(
        "/api/meetings",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
        status=403,
    )

    iam_token.delete()

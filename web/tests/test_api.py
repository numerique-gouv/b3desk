import datetime


def test_api_meetings_nominal(client_app, user, meeting, iam_token):
    res = client_app.get(
        "/api/meetings", headers={"Authorization": f"Bearer {iam_token.access_token}"}
    )

    assert res.json == {
        "meetings": [
            {
                "PIN": "111111111",
                "attendee_url": "http://localhost:5000/meeting/signin/invite/1/creator/1/hash/9120d7b37d540816e62bea4703bf0376b69297c5",
                "moderator_url": "http://localhost:5000/meeting/signin/moderateur/1/creator/1/hash/09aa80a2801e126893b2ce209df71cb7281561eb",
                "name": "meeting",
                "phone_number": "+33bbbphonenumber",
            }
        ]
    }


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

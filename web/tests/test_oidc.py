import time

import pytest
import requests
from authlib.oidc.core import UserInfo
from b3desk import oauth
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet
from joserfc.jwk import RSAKey


@pytest.fixture
def userinfo_key():
    return RSAKey.generate_key(2048, parameters={"kid": "userinfo-key"})


def signed_userinfo_response(key, claims):
    response = requests.Response()
    response.status_code = 200
    response.headers["Content-Type"] = "application/jwt"
    response._content = jwt.encode(
        {"alg": "RS256", "kid": "userinfo-key"}, claims, key
    ).encode()
    return response


def userinfo_claims(iam_client, **kwargs):
    return {
        "iss": oauth.default.load_server_metadata()["issuer"],
        "aud": iam_client.client_id,
        "iat": int(time.time()),
        "exp": int(time.time()) + 60,
        "sub": "alice",
        "given_name": "Alice",
        "usual_name": "Cooper",
        **kwargs,
    }


def test_userinfo_signed_jwt(client_app, iam_client, userinfo_key, mocker):
    """Userinfo responses signed as a JWT are verified and decoded."""
    with client_app.app.test_request_context():
        claims = userinfo_claims(iam_client)
        mocker.patch.object(
            oauth.default,
            "fetch_jwk_set",
            return_value=KeySet([userinfo_key]).as_dict(private=False),
        )
        mocker.patch.object(
            oauth.default,
            "get",
            return_value=signed_userinfo_response(userinfo_key, claims),
        )

        userinfo = oauth.default.userinfo(token={"access_token": "token"})

    assert userinfo["sub"] == "alice"
    assert userinfo["usual_name"] == "Cooper"


def test_userinfo_signed_jwt_clock_skew(client_app, iam_client, userinfo_key, mocker):
    """Signed userinfo responses are accepted when the provider clock is slightly ahead."""
    with client_app.app.test_request_context():
        claims = userinfo_claims(iam_client, iat=int(time.time()) + 60)
        mocker.patch.object(
            oauth.default,
            "fetch_jwk_set",
            return_value=KeySet([userinfo_key]).as_dict(private=False),
        )
        mocker.patch.object(
            oauth.default,
            "get",
            return_value=signed_userinfo_response(userinfo_key, claims),
        )

        userinfo = oauth.default.userinfo(token={"access_token": "token"})

    assert userinfo["sub"] == "alice"


def test_userinfo_signed_jwt_key_rotation(client_app, iam_client, userinfo_key, mocker):
    """The provider keys are fetched again when the userinfo is signed with a new key."""
    old_key = RSAKey.generate_key(2048, parameters={"kid": "old-key"})
    with client_app.app.test_request_context():
        claims = userinfo_claims(iam_client)
        fetch_jwk_set = mocker.patch.object(
            oauth.default,
            "fetch_jwk_set",
            side_effect=[
                KeySet([old_key]).as_dict(private=False),
                KeySet([userinfo_key]).as_dict(private=False),
            ],
        )
        mocker.patch.object(
            oauth.default,
            "get",
            return_value=signed_userinfo_response(userinfo_key, claims),
        )

        userinfo = oauth.default.userinfo(token={"access_token": "token"})

    assert userinfo["sub"] == "alice"
    fetch_jwk_set.assert_called_with(force=True)


def test_userinfo_signed_jwt_wrong_audience(
    client_app, iam_client, userinfo_key, mocker
):
    """Signed userinfo responses issued for another client are rejected."""
    with client_app.app.test_request_context():
        claims = userinfo_claims(iam_client, aud="other-client")
        mocker.patch.object(
            oauth.default,
            "fetch_jwk_set",
            return_value=KeySet([userinfo_key]).as_dict(private=False),
        )
        mocker.patch.object(
            oauth.default,
            "get",
            return_value=signed_userinfo_response(userinfo_key, claims),
        )

        with pytest.raises(JoseError):
            oauth.default.userinfo(token={"access_token": "token"})


def test_api_accepts_signed_userinfo_for_other_clients(
    client_app, iam_client, iam_token, userinfo_key, mocker
):
    """API tokens issued to other clients are accepted with a signed userinfo."""
    with client_app.app.test_request_context():
        claims = userinfo_claims(
            iam_client, aud="other-client", email="alice@example.test"
        )
    mocker.patch.object(
        oauth.default,
        "fetch_jwk_set",
        return_value=KeySet([userinfo_key]).as_dict(private=False),
    )
    mocker.patch.object(
        oauth.default,
        "get",
        return_value=signed_userinfo_response(userinfo_key, claims),
    )

    response = client_app.get(
        "/api/meetings",
        headers={"Authorization": f"Bearer {iam_token.access_token}"},
        status=200,
    )

    assert response.json == {"meetings": []}


def test_userinfo_signed_jwt_wrong_signature(
    client_app, iam_client, userinfo_key, mocker
):
    """Userinfo responses signed with an unknown key are rejected."""
    other_key = RSAKey.generate_key(2048, parameters={"kid": "userinfo-key"})
    with client_app.app.test_request_context():
        claims = userinfo_claims(iam_client)
        mocker.patch.object(
            oauth.default,
            "fetch_jwk_set",
            return_value=KeySet([other_key]).as_dict(private=False),
        )
        mocker.patch.object(
            oauth.default,
            "get",
            return_value=signed_userinfo_response(userinfo_key, claims),
        )

        with pytest.raises(JoseError):
            oauth.default.userinfo(token={"access_token": "token"})


def login(client_app, iam_server):
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    response = client_app.get("/login", status=302)
    response = iam_server.test_client.get(response.location)
    return client_app.get(response.headers["Location"], status=302), iam_user


def test_login_reads_the_userinfo_endpoint(client_app, iam_server, mocker):
    """Claims returned only by the userinfo endpoint are stored in the session."""
    userinfo = oauth.default.userinfo

    def userinfo_with_usual_name(**kwargs):
        return UserInfo({**userinfo(**kwargs), "usual_name": "Cooper"})

    mocker.patch.object(oauth.default, "userinfo", side_effect=userinfo_with_usual_name)

    response, _ = login(client_app, iam_server)

    assert response.location == "/welcome"
    with client_app.session_transaction() as session:
        assert session["userinfo"]["usual_name"] == "Cooper"


def test_login_rejects_userinfo_with_another_subject(client_app, iam_server, mocker):
    """Login fails when the userinfo subject differs from the ID token subject."""
    mocker.patch.object(
        oauth.default, "userinfo", return_value=UserInfo({"sub": "mallory"})
    )

    response, _ = login(client_app, iam_server)

    assert response.location.endswith("/home")
    response.follow().mustcontain("La connexion a été annulée.")
    with client_app.session_transaction() as session:
        assert "userinfo" not in session


def test_login_when_the_userinfo_endpoint_fails(client_app, iam_server, mocker):
    """Login fails without error page when the userinfo endpoint is unreachable."""
    mocker.patch.object(
        oauth.default,
        "userinfo",
        side_effect=requests.ConnectionError("unreachable"),
    )

    response, _ = login(client_app, iam_server)

    assert response.location.endswith("/home")
    response.follow().mustcontain(
        "La connexion a échoué, merci de réessayer plus tard."
    )
    with client_app.session_transaction() as session:
        assert "userinfo" not in session


def test_attendee_authentication_when_the_userinfo_endpoint_fails(
    client_app, iam_server, mocker
):
    """Attendee authentication fails without error page when the userinfo endpoint is unreachable."""
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)
    mocker.patch.object(
        oauth.attendee,
        "userinfo",
        side_effect=requests.ConnectionError("unreachable"),
    )

    response = client_app.get("/meeting/join/1/authenticated", status=302)
    response = iam_server.test_client.get(response.location)
    response = client_app.get(response.headers["Location"], status=302)

    assert response.location == "/"
    with client_app.session_transaction() as session:
        assert "attendee_userinfo" not in session


def test_identity_provider_requests_have_a_timeout(client_app, iam_server, mocker):
    """Requests to the identity provider cannot block forever."""
    request = mocker.spy(requests.Session, "request")

    login(client_app, iam_server)

    assert request.call_count > 0
    for call in request.call_args_list:
        assert call.kwargs.get("timeout") == 5

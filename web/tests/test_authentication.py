from urllib.parse import parse_qs
from urllib.parse import urlparse

import pytest
from b3desk.models import db
from b3desk.models.users import User
from flask import url_for


def test_user_authentication(
    client_app,
    configuration,
    iam_server,
    iam_client,
):
    """Test that user authentication flow works correctly."""
    client_app.app.config["ENABLE_LASUITENUMERIQUE"] = False
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 0

    response = client_app.get("/home")
    response.mustcontain("S’identifier")
    response.mustcontain(no="se déconnecter")

    response = client_app.get("/welcome", status=302)
    response = client_app.get(response.location, status=302)
    response = iam_server.test_client.get(response.location)
    assert response.status_code == 302

    response = client_app.get(response.headers["Location"], status=302)
    response = response.follow(status=200)
    response.mustcontain(no="S’identifier")
    response.mustcontain("se déconnecter")

    user = db.session.get(User, 1)
    assert user.email == iam_user.emails[0]
    assert user.given_name == iam_user.given_name
    assert user.family_name == iam_user.family_name


def test_lasuite_user_authentication(
    client_app,
    configuration,
    iam_server,
    iam_client,
):
    """Test that LaSuite authentication flow works correctly."""
    client_app.app.config["ENABLE_LASUITENUMERIQUE"] = True
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    assert db.session.scalar(db.select(db.func.count()).select_from(User)) == 0

    response = client_app.get("/home")
    response.mustcontain("Se connecter ou créer un compte")
    response.mustcontain(no="se déconnecter")

    response = client_app.get("/welcome", status=302)
    response = client_app.get(response.location, status=302)
    response = iam_server.test_client.get(response.location)
    assert response.status_code == 302

    response = client_app.get(response.headers["Location"], status=302)
    response = response.follow(status=200)
    response.mustcontain(no="Se connecter ou créer un compte")
    response.mustcontain("se déconnecter")

    user = db.session.get(User, 1)
    assert user.email == iam_user.emails[0]
    assert user.given_name == iam_user.given_name
    assert user.family_name == iam_user.family_name


def test_user_goes_back_to_requested_page_after_login(
    client_app, configuration, iam_server, iam_client
):
    """After login, users land on the page they requested before authenticating."""
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    response = client_app.get("/meeting/new?type=quick", status=302)
    response = client_app.get(response.location, status=302)
    response = iam_server.test_client.get(response.location)
    response = client_app.get(response.headers["Location"], status=302)

    assert response.location == "/meeting/new?type=quick"


@pytest.mark.parametrize(
    "next_url",
    [
        "https://evil.test/",
        "//evil.test/",
        "/\\evil.test/",
        "/\t/evil.test/",
        "/\n/evil.test/",
        "evil.test",
    ],
)
def test_login_ignores_external_next_url(
    client_app, configuration, iam_server, iam_client, next_url
):
    """External URLs in the next parameter are ignored, and users land on the welcome page."""
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    response = client_app.get("/login", params={"next": next_url}, status=302)
    response = iam_server.test_client.get(response.location)
    response = client_app.get(response.headers["Location"], status=302)

    assert response.location == "/welcome"


def test_clear_session_after_logout(
    client_app,
    configuration,
    iam_server,
    iam_client,
    iam_token,
):
    """Test logout clear user session."""
    with client_app.session_transaction() as session:
        session["id_token"] = ""
        session["userinfo"] = {
            "email": "alice@domain.tld",
            "family_name": "Cooper",
            "given_name": "Alice",
            "preferred_username": "alice",
        }
    client_app.get("/logout")

    with client_app.session_transaction() as session:
        assert "id_token" not in session
        assert "userinfo" not in session


def test_authorize_tampered_state_redirects_home(
    client_app, configuration, iam_server, iam_client
):
    """A tampered OIDC state on callback must redirect to home with a flash error."""
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    response = client_app.get("/welcome", status=302)
    response = client_app.get(response.location, status=302)
    response = iam_server.test_client.get(response.location)

    tampered_location = response.headers["Location"].replace("state=", "state=wrong-")
    response = client_app.get(tampered_location, status=302)

    assert response.location.endswith("/home")
    response.follow().mustcontain(
        "Votre session de connexion a expiré, merci de réessayer."
    )


def test_authorize_oauth_error_redirects_home(
    client_app, configuration, iam_server, iam_client
):
    """A refused consent on oauth authorize must redirect to home."""
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    response = client_app.get("/welcome", status=302)
    response = client_app.get(response.location, status=302)
    response = iam_server.test_client.get(response.location)

    location = response.headers["Location"].replace(
        "code=", "error=access_denied&code="
    )
    response = client_app.get(location, status=302)

    assert response.location.endswith("/home")
    response.follow().mustcontain("La connexion a été annulée.")


def test_attendee_callback_mismatching_state_redirects_home(
    client_app, configuration, iam_server, iam_client
):
    """A tampered OIDC state on the attendee callback must redirect to home."""
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    response = client_app.get("/meeting/join/1/authenticated", status=302)
    response = iam_server.test_client.get(response.location)

    tampered_location = response.headers["Location"].replace("state=", "state=wrong-")
    response = client_app.get(tampered_location, status=302)

    assert response.location.endswith("/home")
    response.follow().mustcontain(
        "Votre session de connexion a expiré, merci de réessayer."
    )


def test_attendee_callback_oauth_error_redirects_home(
    client_app, configuration, iam_server, iam_client
):
    """A refused consent on the attendee callback must redirect to home."""
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    response = client_app.get("/meeting/join/1/authenticated", status=302)
    response = iam_server.test_client.get(response.location)

    location = response.headers["Location"].replace(
        "code=", "error=access_denied&code="
    )
    response = client_app.get(location, status=302)

    assert response.location.endswith("/")
    response.follow(status=302).follow().mustcontain("La connexion a été annulée.")


def test_organizer_and_attendee_share_the_redirect_uri(
    client_app, configuration, iam_server, iam_client
):
    """Organizers and attendees are redirected to /oidc_callback after authentication."""
    response = client_app.get("/login", status=302)
    params = parse_qs(urlparse(response.location).query)
    assert params["redirect_uri"] == ["http://b3desk.test/oidc_callback"]

    response = client_app.get("/meeting/join/1/authenticated", status=302)
    params = parse_qs(urlparse(response.location).query)
    assert params["redirect_uri"] == ["http://b3desk.test/oidc_callback"]


def test_attendee_authentication(client_app, configuration, iam_server, iam_client):
    """Attendees go back to the meeting after authenticating through /oidc_callback."""
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    response = client_app.get("/meeting/join/1/authenticated", status=302)
    response = iam_server.test_client.get(response.location)
    assert response.headers["Location"].startswith("http://b3desk.test/oidc_callback")

    response = client_app.get(response.headers["Location"], status=302)
    assert response.location == "/meeting/join/1/authenticated"

    with client_app.session_transaction() as session:
        assert session["attendee_userinfo"]["sub"] == iam_user.user_name
        assert "userinfo" not in session


def test_logout_redirects_to_end_session_endpoint(
    client_app, configuration, iam_server, iam_client
):
    """A logout with an active id_token must redirect to the IdP's end_session_endpoint."""
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    response = client_app.get("/welcome", status=302)
    response = client_app.get(response.location, status=302)
    response = iam_server.test_client.get(response.location)
    response = client_app.get(response.headers["Location"], status=302)
    response.follow(status=200)

    with client_app.session_transaction() as session:
        id_token = session["id_token"]

    response = client_app.get("/logout", status=302)

    parsed = urlparse(response.location)
    assert (
        f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        == f"{iam_server.url}oauth/end_session"
    )

    params = parse_qs(parsed.query)
    assert params["id_token_hint"] == [id_token]

    with client_app.app.test_request_context():
        expected_redirect = url_for("public.logout", _external=True)
    assert params["post_logout_redirect_uri"] == [expected_redirect]


def test_unusable_claims_clear_the_session(client_app, caplog):
    """A session whose claims cannot build a user is cleared instead of breaking every page."""
    with client_app.session_transaction() as session:
        session["userinfo"] = {"given_name": "Alice", "family_name": "Cooper"}

    res = client_app.get("/welcome", status=302)
    assert res.location.endswith("/home")
    res.follow(status=200).mustcontain("Votre session est invalide")

    with client_app.session_transaction() as session:
        assert "userinfo" not in session

    assert "Could not build a user from the OIDC claims" in caplog.text

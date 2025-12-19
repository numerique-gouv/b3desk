from flask import abort
from flask import url_for
from flask_webtest import TestApp


def test_custom_400(client_app):
    """Test that custom 400 error page displays correctly."""

    @client_app.app.route("/custom_400")
    def custom_400():
        abort(400, "custom error message")

    response = client_app.get("/custom_400", status=400)
    response.mustcontain("Erreur 400")
    response.mustcontain("custom error message")


def test_custom_404(client_app):
    """Test that custom 404 error page displays correctly."""
    response = client_app.get("/invalid-url", status=404)
    response.mustcontain("Erreur 404")


def test_custom_403(client_app):
    """Test that custom 403 error page displays correctly."""

    @client_app.app.route("/custom_403")
    def custom_403():
        abort(403)

    response = client_app.get("/custom_403", status=403)
    response.mustcontain("Erreur 403")


def test_custom_500(client_app):
    """Test that custom 500 error page displays correctly."""

    @client_app.app.route("/custom_500")
    def custom_500():
        abort(500)

    response = client_app.get("/custom_500", status=500)
    response.mustcontain("Erreur 500")


def test_root__anonymous_user(client_app):
    """Test that anonymous user is redirected to home page."""
    response = client_app.get("/", status=302)

    assert "/home" in response.location


def test_root__authenticated_user(client_app, authenticated_user):
    """Test that authenticated user is redirected to welcome page."""
    response = client_app.get("/", status=302)

    assert "/welcome" in response.location


def test_home__anonymous_user(client_app, mocker):
    """Test that home page displays correctly for anonymous users."""
    STATS = {
        "participantCount": 123,
        "runningCount": 33,
    }
    mocker.patch("b3desk.endpoints.public.get_meetings_stats", return_value=STATS)

    response = client_app.get(
        "/home", extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=200
    )

    assert response.template == "index.html"


def test_home__authenticated_user(client_app, mocker, authenticated_user):
    """Test that authenticated user is redirected to welcome page from home."""
    STATS = {
        "participantCount": 123,
        "runningCount": 33,
    }
    mocker.patch("b3desk.endpoints.public.get_meetings_stats", return_value=STATS)

    response = client_app.get(
        "/home", extra_environ={"REMOTE_ADDR": "127.0.0.1"}, status=302
    )

    assert response.location == url_for("public.welcome")


def test_change_language(app):
    """Test that language can be changed and persists in session."""
    client_app = TestApp(app)
    res = client_app.get("/faq?lang=fr", status=200)
    assert res.session["lang"] == "fr"

    res = client_app.get("/faq?lang=en", status=200)
    assert res.session["lang"] == "en"

    res = client_app.get("/faq", status=200)
    assert res.session["lang"] == "en"


def test_change_language_rejects_invalid_locales(app):
    """Test that invalid language values are rejected to prevent injection."""
    client_app = TestApp(app)
    res = client_app.get("/faq?lang=fr", status=200)
    assert res.session["lang"] == "fr"

    res = client_app.get("/faq?lang=invalid", status=200)
    assert res.session["lang"] == "fr"

    res = client_app.get("/faq?lang='\"efx", status=200)
    assert res.session["lang"] == "fr"


def test_faq__anonymous_user(client_app):
    """Test that FAQ page displays without user name for anonymous users."""
    response = client_app.get("/faq", status=200)

    response.mustcontain(no="Alice Cooper")


def test_faq__authenticated_user(client_app, authenticated_user):
    """Test that FAQ page displays with user name for authenticated users."""
    response = client_app.get("/faq", status=200)

    response.mustcontain("Alice Cooper")


def test_documentation__anonymous_user(client_app, mocker):
    """Test that documentation page displays without user name for anonymous users."""
    client_app.app.config["DOCUMENTATION_LINK"]["url"] = "/documentation"
    client_app.app.config["DOCUMENTATION_LINK"]["is_external"] = False
    response = client_app.get("/documentation", status=200)

    response.mustcontain(no="Alice Cooper")


def test_documentation__authenticated_user(client_app, authenticated_user):
    """Test that documentation page displays with user name for authenticated users."""
    client_app.app.config["DOCUMENTATION_LINK"]["url"] = "/documentation"
    client_app.app.config["DOCUMENTATION_LINK"]["is_external"] = False
    response = client_app.get("/documentation", status=200)

    response.mustcontain("Alice Cooper")


def test_documentation_with_redirection(client_app):
    """Test that external documentation link redirects correctly."""
    client_app.app.config["DOCUMENTATION_LINK"]["url"] = (
        "https://documentation_redirect.ion"
    )
    client_app.app.config["DOCUMENTATION_LINK"]["is_external"] = True
    response = client_app.get("/documentation", status=302)

    response.mustcontain(client_app.app.config["DOCUMENTATION_LINK"]["url"])


def test_accessibilite__anonymous_user(client_app):
    """Test that accessibility page displays without user name for anonymous users."""
    response = client_app.get("/accessibilite", status=200)

    response.mustcontain(no="Alice Cooper")


def test_accessibilite__authenticated_user(client_app, authenticated_user):
    """Test that accessibility page displays with user name for authenticated users."""
    response = client_app.get("/accessibilite", status=200)

    response.mustcontain("Alice Cooper")


def test_mentions_legales__anonymous_user(client_app):
    """Test that legal notices page displays without user name for anonymous users."""
    response = client_app.get("/mentions_legales", status=200)

    response.mustcontain(no="Alice Cooper")


def test_mentions_legales__authenticated_user(client_app, authenticated_user):
    """Test that legal notices page displays with user name for authenticated users."""
    response = client_app.get("/mentions_legales", status=200)

    response.mustcontain("Alice Cooper")


def test_cgu__anonymous_user(client_app):
    """Test that terms of use page displays without user name for anonymous users."""
    response = client_app.get("/cgu", status=200)

    response.mustcontain(no="Alice Cooper")


def test_cgu__authenticated_user(client_app, authenticated_user):
    """Test that terms of use page displays with user name for authenticated users."""
    response = client_app.get("/cgu", status=200)

    response.mustcontain("Alice Cooper")


def test_donnees_personnelles__anonymous_user(client_app):
    """Test that personal data page displays without user name for anonymous users."""
    response = client_app.get("/donnees_personnelles", status=200)

    response.mustcontain(no="Alice Cooper")


def test_donnees_personnelles__authenticated_user(client_app, authenticated_user):
    """Test that personal data page displays with user name for authenticated users."""
    response = client_app.get("/donnees_personnelles", status=200)

    response.mustcontain("Alice Cooper")

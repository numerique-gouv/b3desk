from flask import session


def test_root__anonymous_user(client_app):
    response = client_app.get("/")

    assert response.status_code == 302
    assert "/home" in response.location


def test_root__authenticated_user(client_app, authenticated_user):
    response = client_app.get("/")

    assert response.status_code == 302
    assert "/welcome" in response.location


def test_home__anonymous_user(client_app, mocker):
    STATS = {
        "participantCount": 123,
        "runningCount": 33,
    }
    mocker.patch("flaskr.routes.get_meetings_stats", return_value=STATS)

    response = client_app.get("/home", extra_environ={"REMOTE_ADDR": "127.0.0.1"})

    assert response.status_code == 200
    response.mustcontain("<!-- test page home -->")


def test_home__authenticated_user(client_app, mocker, authenticated_user):
    STATS = {
        "participantCount": 123,
        "runningCount": 33,
    }
    mocker.patch("flaskr.routes.get_meetings_stats", return_value=STATS)

    response = client_app.get("/home", extra_environ={"REMOTE_ADDR": "127.0.0.1"})

    assert response.status_code == 200
    response.mustcontain("<!-- test page home -->")


def test_change_language(client_app):
    response = client_app.get("/faq?lang=fr")
    assert response.status_code == 200
    with client_app.session_transaction() as session:
        assert session["lang"] == "fr"

    response = client_app.get("/faq?lang=uk")
    assert response.status_code == 200
    with client_app.session_transaction() as session:
        assert session["lang"] == "uk"

    response = client_app.get("/faq")
    assert response.status_code == 200
    with client_app.session_transaction() as session:
        assert session["lang"] == "uk"


def test_faq__anonymous_user(client_app):
    response = client_app.get("/faq")

    assert response.status_code == 200
    response.mustcontain(no="Alice Cooper")


def test_faq__authenticated_user(client_app, authenticated_user):
    response = client_app.get("/faq")

    assert response.status_code == 200
    response.mustcontain("Alice Cooper")


def test_documentation__anonymous_user(app, client_app, mocker):
    app.config["DOCUMENTATION_LINK"]["url"] = "/documentation"
    app.config["DOCUMENTATION_LINK"]["is_external"] = False
    response = client_app.get("/documentation")

    assert response.status_code == 200
    response.mustcontain(no="Alice Cooper")


def test_documentation__authenticated_user(app, client_app, authenticated_user):
    app.config["DOCUMENTATION_LINK"]["url"] = "/documentation"
    app.config["DOCUMENTATION_LINK"]["is_external"] = False
    response = client_app.get("/documentation")

    assert response.status_code == 200
    response.mustcontain("Alice Cooper")


def test_documentation_with_redirection(app, client_app):
    app.config["DOCUMENTATION_LINK"]["url"] = "https://documentation_redirect.ion"
    app.config["DOCUMENTATION_LINK"]["is_external"] = True
    response = client_app.get("/documentation")

    assert response.status_code == 302
    response.mustcontain(app.config["DOCUMENTATION_LINK"]["url"])


def test_accessibilite__anonymous_user(client_app):
    response = client_app.get("/accessibilite")

    assert response.status_code == 200
    response.mustcontain(no="Alice Cooper")


def test_accessibilite__authenticated_user(client_app, authenticated_user):
    response = client_app.get("/accessibilite")

    assert response.status_code == 200
    response.mustcontain("Alice Cooper")


def test_mentions_legales__anonymous_user(client_app):
    response = client_app.get("/mentions_legales")

    assert response.status_code == 200
    response.mustcontain(no="Alice Cooper")


def test_mentions_legales__authenticated_user(client_app, authenticated_user):
    response = client_app.get("/mentions_legales")

    assert response.status_code == 200
    response.mustcontain("Alice Cooper")


def test_cgu__anonymous_user(client_app):
    response = client_app.get("/cgu")

    assert response.status_code == 200
    response.mustcontain(no="Alice Cooper")


def test_cgu__authenticated_user(client_app, authenticated_user):
    response = client_app.get("/cgu")

    assert response.status_code == 200
    response.mustcontain("Alice Cooper")


def test_donnees_personnelles__anonymous_user(client_app):
    response = client_app.get("/donnees_personnelles")

    assert response.status_code == 200
    response.mustcontain(no="Alice Cooper")


def test_donnees_personnelles__authenticated_user(client_app, authenticated_user):
    response = client_app.get("/donnees_personnelles")

    assert response.status_code == 200
    response.mustcontain("Alice Cooper")

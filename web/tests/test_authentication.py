from b3desk.models import db
from b3desk.models.users import User


def test_user_authentication(
    client_app,
    configuration,
    iam_server,
    iam_client,
):
    client_app.app.config["ENABLE_LASUITENUMERIQUE"] = False
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    assert not User.query.all()

    res = client_app.get("/home")
    res.mustcontain("S’identifier")
    res.mustcontain(no="se déconnecter")

    # 1. attempt to access a protected page
    res1 = client_app.get("/welcome", status=302)

    # 2. authorization code request
    res2 = iam_server.test_client.get(res1.location)
    assert res2.status_code == 302

    # 3. load your application authorization endpoint
    # pyoidc produces a useless error message there
    # https://github.com/CZ-NIC/pyoidc/issues/824
    res3 = client_app.get(res2.headers["Location"], status=302, expect_errors=True)

    # 4. redirect to the protected page
    res4 = res3.follow(status=200)
    res4.mustcontain(no="S’identifier")
    res4.mustcontain("se déconnecter")

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
    client_app.app.config["ENABLE_LASUITENUMERIQUE"] = True
    iam_user = iam_server.random_user()
    iam_server.login(iam_user)
    iam_server.consent(iam_user)

    assert not User.query.all()

    res = client_app.get("/home")
    res.mustcontain("Se connecter ou créer un compte")
    res.mustcontain(no="se déconnecter")

    # 1. attempt to access a protected page
    res1 = client_app.get("/welcome", status=302)

    # 2. authorization code request
    res2 = iam_server.test_client.get(res1.location)
    assert res2.status_code == 302

    # 3. load your application authorization endpoint
    # pyoidc produces a useless error message there
    # https://github.com/CZ-NIC/pyoidc/issues/824
    res3 = client_app.get(res2.headers["Location"], status=302, expect_errors=True)

    # 4. redirect to the protected page
    res4 = res3.follow(status=200)
    res4.mustcontain(no="Se connecter ou créer un compte")
    res4.mustcontain("se déconnecter")

    user = db.session.get(User, 1)
    assert user.email == iam_user.emails[0]
    assert user.given_name == iam_user.given_name
    assert user.family_name == iam_user.family_name

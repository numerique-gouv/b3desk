from b3desk import create_app

from tests.html_validation import ValidatingTestApp


def test_security_headers(client_app):
    res = client_app.get("/", status=302)
    assert (
        res.headers["Content-Security-Policy"]
        == "frame-ancestors 'self'; default-src 'self'; script-src 'self'; frame-src 'self' https://podeduc.apps.education.fr; img-src 'self' data: https://bbb.test; connect-src 'self'; font-src 'self'; style-src 'self'"
    )


def test_security_headers_with_available_nextcloud(
    client_app, nextcloud_credentials, authenticated_user
):
    res = client_app.get("/", status=302)
    assert (
        res.headers["Content-Security-Policy"]
        == f"frame-ancestors 'self'; default-src 'self'; script-src 'self'; frame-src 'self' https://podeduc.apps.education.fr; img-src 'self' data: https://bbb.test; connect-src 'self' {authenticated_user.nc_locator}; font-src 'self'; style-src 'self'"
    )


def test_security_headers_with_matomo_url_in_settings(configuration):
    matomo_url = "http://matomo.example.com"
    configuration["MATOMO_URL"] = matomo_url
    app = create_app(configuration)
    with app.test_request_context():
        client_app = ValidatingTestApp(app)
        res = client_app.get("/", status=302)
        assert (
            res.headers["Content-Security-Policy"]
            == f"frame-ancestors 'self'; default-src 'self'; script-src 'self' {matomo_url}; frame-src 'self' https://podeduc.apps.education.fr; img-src 'self' data: {matomo_url} https://bbb.test; connect-src 'self' {matomo_url}; font-src 'self'; style-src 'self'"
        )


def test_security_headers_with_satisfaction_poll_url_in_settings(configuration):
    satisfaction_poll_url = "http://satisfaction.example.com"
    configuration["SATISFACTION_POLL_URL"] = satisfaction_poll_url
    app = create_app(configuration)
    with app.test_request_context():
        client_app = ValidatingTestApp(app)
        res = client_app.get("/", status=302)
        assert (
            res.headers["Content-Security-Policy"]
            == f"frame-ancestors 'self'; default-src 'self'; script-src 'self'; frame-src 'self' https://podeduc.apps.education.fr {satisfaction_poll_url}; img-src 'self' data: https://bbb.test; connect-src 'self'; font-src 'self'; style-src 'self'"
        )


def test_security_headers_with_enable_lasuite(configuration):
    lasuite_url = "https://integration.lasuite.numerique.gouv.fr"
    configuration["ENABLE_LASUITENUMERIQUE"] = True
    app = create_app(configuration)
    with app.test_request_context():
        client_app = ValidatingTestApp(app)
        res = client_app.get("/", status=302)
        assert (
            res.headers["Content-Security-Policy"]
            == f"frame-ancestors 'self'; default-src 'self'; script-src 'self' {lasuite_url}; frame-src 'self' https://podeduc.apps.education.fr; img-src 'self' data: {lasuite_url} https://bbb.test; connect-src 'self' {lasuite_url}; font-src 'self' {lasuite_url}; style-src 'self' {lasuite_url} 'unsafe-inline'"
        )


def test_security_headers_without_bbb_url(configuration):
    configuration["BIGBLUEBUTTON_ENDPOINT"] = None
    app = create_app(configuration)
    with app.test_request_context():
        client_app = ValidatingTestApp(app)
        res = client_app.get("/", status=302)
        assert (
            res.headers["Content-Security-Policy"]
            == "frame-ancestors 'self'; default-src 'self'; script-src 'self'; frame-src 'self' https://podeduc.apps.education.fr; img-src 'self' data:; connect-src 'self'; font-src 'self'; style-src 'self'"
        )


def test_integral_security_headers(configuration):
    matomo_url = "http://matomo.example.com"
    configuration["MATOMO_URL"] = matomo_url
    satisfaction_poll_url = "http://satisfaction.example.com"
    configuration["SATISFACTION_POLL_URL"] = satisfaction_poll_url
    lasuite_url = "https://integration.lasuite.numerique.gouv.fr"
    configuration["ENABLE_LASUITENUMERIQUE"] = True
    app = create_app(configuration)
    with app.test_request_context():
        client_app = ValidatingTestApp(app)
        res = client_app.get("/", status=302)
        assert (
            res.headers["Content-Security-Policy"]
            == f"frame-ancestors 'self'; default-src 'self'; script-src 'self' {matomo_url} {lasuite_url}; frame-src 'self' https://podeduc.apps.education.fr {satisfaction_poll_url}; img-src 'self' data: {matomo_url} {lasuite_url} https://bbb.test; connect-src 'self' {matomo_url} {lasuite_url}; font-src 'self' {lasuite_url}; style-src 'self' {lasuite_url} 'unsafe-inline'"
        )

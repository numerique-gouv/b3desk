import json
from unittest import mock

import requests
from b3desk.endpoints.captcha import captcha_validation
from b3desk.endpoints.captcha import captchetat_service_status
from b3desk.endpoints.captcha import get_captchetat_token
from b3desk.session import should_display_captcha


class Access_token_response:
    def __init__(self, status_code):
        self.json_data = {
            "access_token": "valid-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "aife.captchetatv2 openid resource.READ piste.captchetat",
        }
        self.status_code = status_code

    def json(self):
        return self.json_data


class Access_token_bad_response:
    def __init__(self, status_code):
        self.json_data = {
            "token_type": "Bearer",
            "expires_in": 3600,
            "scope": "aife.captchetatv2 openid resource.READ piste.captchetat",
        }
        self.status_code = status_code

    def json(self):
        return self.json_data


class Captcha_response:
    def __init__(self, status_code):
        self.json_data = {
            "imageb64": "data:image/png;base64",
            "uuid": "captcha-uuid",
        }
        self.content = b"RIFF\xfa\x1a\x02\x00WAVEfmt"
        self.status_code = status_code

    def json(self):
        return self.json_data


class Captcha_validation_response:
    def __init__(self):
        self.json_data = {"true"}
        self.status_code = 200

    def json(self):
        return self.json_data


class Captcha_validation_bad_response:
    def __init__(self):
        self.status_code = 403


class Captcha_healthcheck_response:
    def __init__(self):
        self.json_data = {
            "status": "UP",
        }
        self.status_code = 200

    def json(self):
        return self.json_data


def test_get_captchetat_token(client_app, mocker):
    mocker.patch("requests.post", return_value=Access_token_response(200))
    access_token = get_captchetat_token()
    assert access_token == "valid-access-token"
    mocker.patch("requests.post", return_value=Access_token_bad_response(200))
    access_token = get_captchetat_token()
    assert access_token == "valid-access-token"


def test_get_captchetat_token_bad_status_code(client_app, mocker, caplog):
    mocker.patch("requests.post", return_value=Access_token_response(401))
    access_token = get_captchetat_token()
    assert not access_token == "valid-access-token"
    assert "captcha error : OAuth access token not received" in caplog.text


def test_get_captchetat_token_bad_response(client_app, mocker, caplog):
    mocker.patch("requests.post", return_value=Access_token_bad_response(200))
    access_token = get_captchetat_token()
    assert not access_token == "valid-access-token"
    assert "captcha error : OAuth access token not received" in caplog.text


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
def test_captcha_proxy(access_token, client_app, mocker):
    access_token.return_value = "valid-access-token"
    mocker.patch("requests.get", return_value=Captcha_response(200))
    captcha_response = Captcha_response(200)
    response = client_app.get(
        "/simple-captcha-endpoint", params={"get": "sound", "c": "captchaFR"}
    )
    assert captcha_response.content == response.body
    response = client_app.get(
        "/simple-captcha-endpoint", params={"get": "image", "c": "captchaFR"}
    )
    assert captcha_response.json() == json.loads(response.body.decode("utf-8"))


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
def test_captcha_proxy_but_captchetat_is_down(access_token, client_app, mocker, caplog):
    access_token.return_value = "valid-access-token"
    mocker.patch("requests.get", side_effect=requests.exceptions.ConnectionError())
    response = client_app.get(
        "/simple-captcha-endpoint",
        params={"get": "sound", "c": "captchaFR"},
        status=503,
    )
    assert json.loads(response.body.decode("utf-8")) == {"success": False}
    assert "Network issue during connection to captchetat" in caplog.text


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
def test_captcha_proxy_with_no_token(access_token, client_app, mocker, caplog):
    access_token.return_value = None
    mocker.patch("requests.get", return_value=Captcha_response(200))
    response = client_app.get(
        "/simple-captcha-endpoint",
        params={"get": "sound", "c": "captchaFR"},
        status=403,
    )
    assert json.loads(response.body.decode("utf-8")) == {"success": False}
    assert "captcha error : Invalid PISTE credentials." in caplog.text


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
def test_captcha_proxy_bad_response(access_token, client_app, mocker, caplog):
    access_token.return_value = "valid-access-token"
    mocker.patch("requests.get", return_value=Captcha_response(401))
    client_app.get("/simple-captcha-endpoint", status=401)
    assert "captcha error : Captcha image/sound not received" in caplog.text


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
def test_captcha_validation(access_token, client_app, mocker):
    access_token.return_value = "valid-access-token"
    mocker.patch("requests.post", return_value=Captcha_validation_response())
    validation = captcha_validation("captcha_uuid", "captcha_code")
    assert validation == {"true"}


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
def test_captcha_validation_but_captchetat_is_down(
    access_token, client_app, mocker, caplog
):
    access_token.return_value = "valid-access-token"
    mocker.patch("requests.post", side_effect=requests.exceptions.ConnectionError())
    validation = captcha_validation("captcha_uuid", "captcha_code")
    assert validation
    assert "Network issue during connection to captchetat" in caplog.text


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
def test_captcha_validation_with_no_token(access_token, client_app, mocker, caplog):
    access_token.return_value = None
    mocker.patch("requests.post", return_value=Captcha_validation_response())
    validation = captcha_validation("captcha_uuid", "captcha_code")
    assert validation
    assert "captcha error : Invalid credentials." in caplog.text


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
def test_captcha_validation_bad_response(access_token, client_app, mocker, caplog):
    access_token.return_value = "valid-access-token"
    mocker.patch("requests.post", return_value=Captcha_validation_bad_response())
    validation = captcha_validation("captcha_uuid", "captcha_code")
    assert validation
    assert "captcha error : An error happened during captcha validation." in caplog.text


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
def test_captchetat_service_status(access_token, client_app, mocker):
    access_token.return_value = "valid-access-token"
    mocker.patch("requests.get", return_value=Captcha_healthcheck_response())
    status = captchetat_service_status()
    assert status == "UP"


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
def test_captchetat_service_status_with_no_token(
    access_token, client_app, mocker, caplog
):
    access_token.return_value = None
    mocker.patch("requests.get", return_value=Captcha_healthcheck_response())
    response = captchetat_service_status()
    assert "captcha error : Invalid credentials." in caplog.text
    assert response == ({"success": False}, 403)


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
@mock.patch("b3desk.endpoints.captcha.captchetat_service_status")
@mock.patch("b3desk.endpoints.join.captcha_validation")
def test_join_with_visio_code_and_captcha_needed(
    captcha_validation,
    status,
    access_token,
    client_app,
    visio_code_session,
    mocker,
    meeting,
):
    client_app.app.config["CAPTCHA_NUMBER_ATTEMPTS"] = 1
    status.return_value = "UP"
    access_token.return_value = "valid-access-token"
    params = {"visio_code1": "123", "visio_code2": "456", "visio_code3": "789"}
    # 1st attempt
    response = client_app.post(
        "/meeting/visio_code",
        params=params,
    )
    assert ("error", "Le code de connexion saisi est erroné") in response.flashes
    response.mustcontain(no="captcha-container")
    # 2nd attempt
    response = client_app.post(
        "/meeting/visio_code",
        params=params,
    )
    assert ("error", "Le code de connexion saisi est erroné") in response.flashes
    response = response.follow()
    response.mustcontain("captcha-container")


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
@mock.patch("b3desk.endpoints.captcha.captchetat_service_status")
@mock.patch("b3desk.endpoints.join.captcha_validation")
def test_join_with_visio_code_with_wrong_visio_code_and_wrong_captcha(
    captcha_validation,
    status,
    access_token,
    client_app,
    visio_code_session,
    mocker,
    meeting,
):
    client_app.app.config["CAPTCHA_NUMBER_ATTEMPTS"] = 1
    status.return_value = "UP"
    access_token.return_value = "valid-access-token"
    captcha_validation.return_value = False

    with client_app.session_transaction() as sess:
        sess["visio_code_attempt_counter"] = 2

    with client_app.app.test_request_context("/"):
        from flask import session

        session.update(sess)
        response = client_app.post(
            "/meeting/visio_code",
            params={
                "visio_code1": "123",
                "visio_code2": "456",
                "visio_code3": "789",
                "captchaCode": "captchaCode",
                "captchetat-uuid": "captchetat-uuid",
            },
        )
        assert ("error", "Le captcha saisi est erroné") in response.flashes
        # the existence of the meeting should not be revealed at this stage
        assert (
            "error",
            "Le code de connexion saisi est erroné",
        ) not in response.flashes


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
@mock.patch("b3desk.endpoints.captcha.captchetat_service_status")
@mock.patch("b3desk.endpoints.join.captcha_validation")
def test_join_with_visio_code_with_wrong_visio_code_and_valid_captcha(
    captcha_validation,
    status,
    access_token,
    client_app,
    visio_code_session,
    mocker,
    meeting,
):
    client_app.app.config["CAPTCHA_NUMBER_ATTEMPTS"] = 1
    status.return_value = "UP"
    access_token.return_value = "valid-access-token"
    captcha_validation.return_value = True

    with client_app.session_transaction() as sess:
        sess["visio_code_attempt_counter"] = 2

    with client_app.app.test_request_context("/"):
        from flask import session

        session.update(sess)
        response = client_app.post(
            "/meeting/visio_code",
            params={
                "visio_code1": "123",
                "visio_code2": "456",
                "visio_code3": "789",
                "captchaCode": "captchaCode",
                "captchetat-uuid": "captchetat-uuid",
            },
        )
        assert ("error", "Le captcha saisi est erroné") not in response.flashes
        assert ("error", "Le code de connexion saisi est erroné") in response.flashes


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
@mock.patch("b3desk.endpoints.captcha.captchetat_service_status")
@mock.patch("b3desk.endpoints.join.captcha_validation")
def test_join_with_visio_code_with_valid_visio_code_and_wrong_captcha(
    captcha_validation,
    status,
    access_token,
    client_app,
    visio_code_session,
    mocker,
    meeting,
):
    client_app.app.config["CAPTCHA_NUMBER_ATTEMPTS"] = 1
    status.return_value = "UP"
    access_token.return_value = "valid-access-token"
    captcha_validation.return_value = False

    with client_app.session_transaction() as sess:
        sess["visio_code_attempt_counter"] = 2

    with client_app.app.test_request_context("/"):
        from flask import session

        session.update(sess)

        response = client_app.post(
            "/meeting/visio_code",
            params={
                "visio_code1": "911",
                "visio_code2": "111",
                "visio_code3": "111",
                "captchaCode": "captchaCode",
                "captchetat-uuid": "captchetat-uuid",
            },
        )
        assert ("error", "Le captcha saisi est erroné") in response.flashes
        assert (
            "error",
            "Le code de connexion saisi est erroné",
        ) not in response.flashes


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
@mock.patch("b3desk.endpoints.captcha.captchetat_service_status")
@mock.patch("b3desk.endpoints.join.captcha_validation")
def test_join_with_visio_code_with_valid_visio_code_and_valid_captcha(
    captcha_validation,
    status,
    access_token,
    client_app,
    visio_code_session,
    mocker,
    meeting,
):
    client_app.app.config["CAPTCHA_NUMBER_ATTEMPTS"] = 1
    status.return_value = "UP"
    access_token.return_value = "valid-access-token"
    captcha_validation.return_value = True

    with client_app.session_transaction() as sess:
        sess["visio_code_attempt_counter"] = 2

    with client_app.app.test_request_context("/"):
        from flask import session

        session.update(sess)

        response = client_app.post(
            "/meeting/visio_code",
            params={
                "visio_code1": "911",
                "visio_code2": "111",
                "visio_code3": "111",
                "captchaCode": "captchaCode",
                "captchetat-uuid": "captchetat-uuid",
            },
        )
        response.mustcontain("Rejoindre le séminaire")


def test_should_display_captcha_with_no_PISTE_OAUTH_CLIENT_ID(client_app):
    client_app.app.config["PISTE_OAUTH_CLIENT_ID"] = None
    assert not should_display_captcha()


def test_should_display_captcha_with_no_PISTE_OAUTH_CLIENT_SECRET(client_app):
    client_app.app.config["PISTE_OAUTH_CLIENT_SECRET"] = None
    assert not should_display_captcha()


def test_should_display_captcha_with_no_CAPTCHETAT_API_URL(client_app):
    client_app.app.config["CAPTCHETAT_API_URL"] = None
    assert not should_display_captcha()


def test_should_display_captcha_with_no_PISTE_OAUTH_API_URL(client_app):
    client_app.app.config["PISTE_OAUTH_API_URL"] = None
    assert not should_display_captcha()


def test_should_display_captcha_with_no_token(client_app, caplog):
    client_app.app.config["CAPTCHA_NUMBER_ATTEMPTS"] = 1

    with client_app.session_transaction() as sess:
        sess["visio_code_attempt_counter"] = 2

    with client_app.app.test_request_context("/"):
        from flask import session

        session.update(sess)

        result = should_display_captcha()
        assert not result
        assert "captcha error : Captchetat service is down" in caplog.text

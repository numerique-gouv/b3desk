import json
from unittest import mock

from b3desk.endpoints.captcha import get_captchetat_token


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


def test_get_captchetat_token(client_app, mocker):
    mocker.patch("requests.post", return_value=Access_token_response(200))
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
def test_captcha_proxy_bad_response(access_token, client_app, mocker, caplog):
    access_token.return_value = "valid-access-token"
    mocker.patch("requests.get", return_value=Captcha_response(401))
    client_app.get("/simple-captcha-endpoint", status=401)
    assert "captcha error : Captcha image/sound not received" in caplog.text


@mock.patch("b3desk.endpoints.captcha.get_captchetat_token")
@mock.patch("b3desk.endpoints.captcha.captchetat_service_status")
def test_join_with_visio_code_and_captcha_needed(
    status, access_token, client_app, visio_code_session, mocker
):
    client_app.app.config["CAPTCHA_NUMBER_ATTEMPTS"] = 1
    status.return_value = "UP"
    access_token.return_value = "valid-access-token"
    response = client_app.post(
        "/meeting/visio_code",
        params={"visio_code1": "123", "visio_code2": "456", "visio_code3": "789"},
    )
    assert ("error", "Le code de connexion saisi est erroné") in response.flashes
    response = client_app.post(
        "/meeting/visio_code",
        params={"visio_code1": "123", "visio_code2": "456", "visio_code3": "789"},
    )
    assert ("error", "Le code de connexion saisi est erroné") in response.flashes
    response = response.follow()
    response.mustcontain("captcha-container")

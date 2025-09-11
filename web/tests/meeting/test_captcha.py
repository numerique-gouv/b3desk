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

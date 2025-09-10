import requests
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from b3desk.utils import captcha_error

bp = Blueprint("captcha", __name__)


def get_captchetat_token():
    url = f"{current_app.config['PISTE_OAUTH_API_URL']}/oauth/token"
    form_data = {
        "grant_type": "client_credentials",
        "client_id": current_app.config["PISTE_OAUTH_CLIENT_ID"],
        "client_secret": current_app.config["PISTE_OAUTH_CLIENT_SECRET"],
        "scope": "piste.captchetat",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=form_data, headers=headers)
    if response.status_code != 200 or "access_token" not in response.json():
        message = f"access token status code : {response.status_code}"
        captcha_error(message)
        current_app.logger.error("Captcha error: OAuth access token not received")
        return
    json_response = response.json()
    return json_response["access_token"]


@bp.route("/simple-captcha-endpoint", methods=["GET"])
def captcha_proxy():
    access_token = get_captchetat_token()
    piste_url = f"{current_app.config['CAPTCHETAT_API_URL']}/captchetat/v2/simple-captcha-endpoint"
    try:
        response = requests.get(
            piste_url,
            params=dict(request.args),
            headers={"Authorization": f"Bearer {access_token}"},
        )
        captcha_info = (
            response.content
            if "sound" == dict(request.args)["get"]
            else response.json()
        )
        return captcha_info
    except:
        message = "Captcha error: Captcha image/sound not received"
        captcha_error(message)
        return


@bp.route("/prepare-captcha-validation", methods=["POST"])
def prepare_captcha_validation():
    data = request.get_json()
    captcha_uuid = data.get("uuid")
    captcha_code = data.get("code")
    return captcha_validation(captcha_uuid, captcha_code)


def captcha_validation(captcha_uuid, captcha_code):
    access_token = get_captchetat_token()
    try:
        response = requests.post(
            f"{current_app.config['CAPTCHETAT_API_URL']}/captchetat/v2/valider-captcha",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"uuid": captcha_uuid, "code": captcha_code},
        )
        return jsonify({"success": response.json()})
    except:
        message = "Captcha error: Captcha response validation not received"
        captcha_error(message)
        return

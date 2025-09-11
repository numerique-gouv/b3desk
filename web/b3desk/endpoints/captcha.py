import json

import requests
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import redirect
from flask import request
from flask import session
from flask import url_for

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
        message = "OAuth access token not received"
        captcha_error(message)
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
        message = "Captcha image/sound not received"
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
        message = "Captcha response validation not received"
        captcha_error(message)
        return


def captcha_error(message):
    session["visio_code_attempt_counter"] = 0
    current_app.logger.error("captcha error : %s", message)
    return redirect(url_for("public.index"))


def captchetat_service_status():
    access_token = get_captchetat_token()
    response = requests.get(
        f"{current_app.config['CAPTCHETAT_API_URL']}/captchetat/v2/healthcheck",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    raw_data = response.content
    json_string = raw_data.decode("utf-8")
    data = json.loads(json_string) if json_string else {"status": "DOWN"}
    return data["status"]

import requests
from flask import Blueprint
from flask import current_app
from flask import request

from b3desk import cache
from b3desk.session import visio_code_attempt_counter_reset

bp = Blueprint("captcha", __name__)
CACHE_KEY_CAPTCHETAT_CREDENTIALS = "captchetat-credentials"


def get_captchetat_token():
    if token := cache.get(CACHE_KEY_CAPTCHETAT_CREDENTIALS):
        return token

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
        return None

    response = response.json()
    token = response["access_token"]
    timeout = response.get("expires_in", 3600)
    cache.set(CACHE_KEY_CAPTCHETAT_CREDENTIALS, token, timeout=timeout)
    return token


@bp.route("/simple-captcha-endpoint", methods=["GET"])
def captcha_proxy():
    """Get the images and sound from the captcha service, and return it to be used by the JS."""
    if not (access_token := get_captchetat_token()):
        captcha_error("Invalid PISTE credentials.")
        return {"success": False}, 403

    piste_url = f"{current_app.config['CAPTCHETAT_API_URL']}/captchetat/v2/simple-captcha-endpoint"
    try:
        response = requests.get(
            piste_url,
            params=dict(request.args),
            headers={"Authorization": f"Bearer {access_token}"},
        )
    except requests.RequestException as exc:
        message = f"Network issue during connection to captchetat {exc}"
        captcha_error(message)
        return {"success": False}, 503

    if response.status_code != 200:
        message = "Captcha image/sound not received"
        captcha_error(message)
        return {"success": False}, response.status_code

    captcha_info = (
        response.content if "sound" == dict(request.args)["get"] else response.json()
    )
    return captcha_info


def captcha_validation(captcha_uuid, captcha_code):
    if not (access_token := get_captchetat_token()):
        captcha_error("Invalid credentials.")
        return True

    try:
        response = requests.post(
            f"{current_app.config['CAPTCHETAT_API_URL']}/captchetat/v2/valider-captcha",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"uuid": captcha_uuid, "code": captcha_code},
        )

    except requests.RequestException as exc:
        message = f"Network issue during connection to captchetat {exc}"
        captcha_error(message)
        return True

    if response.status_code != 200:
        captcha_error("An error happened during captcha validation.")
        return True
    return response.json()


def captcha_error(message):
    """Reset the attempt counter."""
    visio_code_attempt_counter_reset()
    cache.delete(CACHE_KEY_CAPTCHETAT_CREDENTIALS)
    current_app.logger.error("captcha error : %s", message)


def captchetat_service_status():
    """Perform a health check on captchetat."""
    if not (access_token := get_captchetat_token()):
        captcha_error("Invalid credentials.")
        return {"success": False}, 403

    response = requests.get(
        f"{current_app.config['CAPTCHETAT_API_URL']}/captchetat/v2/healthcheck",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    data = response.json()
    return data["status"]

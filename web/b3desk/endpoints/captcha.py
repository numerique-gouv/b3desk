import requests
from flask import Blueprint
from flask import current_app
from flask import flash
from flask import jsonify
from flask import request
from flask import session
from flask_babel import lazy_gettext as _

from b3desk import csrf

bp = Blueprint("captcha", __name__)


def get_captchetat_token():
    url = "https://oauth.piste.gouv.fr/api/oauth/token"
    form_data = {
        "grant_type": "client_credentials",
        "client_id": current_app.config["CLIENT_ID"],
        "client_secret": current_app.config["CLIENT_SECRET"],
        "scope": "piste.captchetat",
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post(url, data=form_data, headers=headers)
    if response.status_code != 200 or "access_token" not in response.json():
        session["visio_code"]["captcha_is_dead"] = True
        flash(_("Erreur Captcha : rechargez la page"), "error")
        return
    else:
        session["visio_code"]["captcha_is_dead"] = False
    json_response = response.json()
    return json_response["access_token"]


@bp.route("/simple-captcha-endpoint", methods=["GET"])
def captcha_proxy():
    access_token = get_captchetat_token()
    piste_url = "https://api.piste.gouv.fr/piste/captchetat/v2/simple-captcha-endpoint"
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
        flash(_("Erreur Captcha : rechargez la page"), "error")
        return


@bp.route("/captcha-validation", methods=["POST"])
@csrf.exempt
def captcha_validation():
    data = request.get_json()
    captcha_uuid = data.get("uuid")
    captcha_code = data.get("code")
    access_token = get_captchetat_token()
    response = requests.post(
        "https://api.piste.gouv.fr/piste/captchetat/v2/valider-captcha",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"uuid": captcha_uuid, "code": captcha_code},
    )
    return jsonify({"success": response.json()})

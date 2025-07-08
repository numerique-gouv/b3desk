import click
from flask import Blueprint
from flask import current_app

from b3desk.models.meetings import delete_all_old_shadow_meetings

bp = Blueprint("commands", __name__, cli_group=None)


@bp.cli.command("get-apps-id")
@click.argument("email")
def get_apps_id(email):
    from b3desk.models.users import get_secondary_identity_provider_id_from_email

    try:
        secondary_id = get_secondary_identity_provider_id_from_email(email)
        current_app.logger.info(
            "ID from secondary identity provider for email %s: %s", email, secondary_id
        )
    except Exception as e:
        current_app.logger.error(e)


@bp.cli.command("delete-old-shadow-meetings")
def delete_old_shadow_meetings():
    delete_all_old_shadow_meetings()


@bp.cli.command("generate-private-key")
def generate_private_key():
    from joserfc.jwk import RSAKey

    saved_private_pem_str = (
        current_app.config["PRIVATE_KEY"] if current_app.config["PRIVATE_KEY"] else None
    )
    if saved_private_pem_str:
        if (
            input(
                "A private-key has already been saved in the settings.\nIf you choose to change the current private-key, all old tokens will become invalid.\nAre you sure you want to create a new private-key? (y/n)"
            )
            != "y"
        ):
            exit()
    private_key = RSAKey.generate_key(2048, parameters={"alg": "RS256", "use": "sig"})
    private_pem_bytes = private_key.as_pem(private=True)
    private_pem_str = private_pem_bytes.decode("utf-8")
    print("private key to save in settings")
    print(private_pem_str)


@bp.cli.command("generate-sip-token")
def generate_sip_token():
    from joserfc.jwk import RSAKey
    from joserfc.jwt import encode

    saved_private_pem_str = (
        current_app.config["PRIVATE_KEY"] if current_app.config["PRIVATE_KEY"] else None
    )
    if saved_private_pem_str is None:
        print("You need to generate and save a private-key")
        exit()
    else:
        try:
            key = RSAKey.import_key(saved_private_pem_str)
            if key.is_private:
                header = {"alg": "RS256", "typ": "JWT"}
                claims = {
                    "iss": f"{current_app.config['PREFERRED_URL_SCHEME']}://{current_app.config['SERVER_NAME']}"
                }
                private_key_from_settings = RSAKey.import_key(
                    current_app.config["PRIVATE_KEY"]
                )
                token = encode(header, claims, private_key_from_settings)
                print("Token JWT to send to SIPMediaGW hardware")
                print(token)
            else:
                print(
                    "Your private-key is invalid. You must generate and save a new one."
                )
        except:
            print("Your private-key is invalid. You must generate and save a new one.")


@bp.cli.command("check-sip-settings")
def check_sip_settings():
    error = False
    from joserfc.jwk import RSAKey

    saved_private_pem_str = (
        current_app.config["PRIVATE_KEY"] if current_app.config["PRIVATE_KEY"] else None
    )
    if not current_app.config["ENABLE_SIP"]:
        print("You need to turn on ENABLE_SIP")
        error = True
    if not current_app.config["FQDN_SIP_SERVER"]:
        print("You need to save the FQDN_SIP_SERVER")
        error = True
    if saved_private_pem_str is None:
        print("You need to generate and save a private-key")
        error = True
    try:
        key = RSAKey.import_key(saved_private_pem_str)
        if not key.is_private:
            print("Your private-key is invalid. You must generate and save a new one.")
            error = True
    except:
        print("Your private-key is invalid. You must generate and save a new one.")
        error = True
    if not error:
        print("SIPMediaGW settings are OK.")

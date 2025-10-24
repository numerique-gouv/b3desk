import click
from flask import Blueprint
from flask import current_app

from b3desk.models.meetings import delete_all_old_shadow_meetings

bp = Blueprint("commands", __name__, cli_group=None)


@bp.cli.command("get-apps-id")
@click.argument("email")
def get_apps_id(email):
    """CLI command to retrieve user ID from secondary identity provider using email."""
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
    """CLI command to delete expired shadow meetings from database."""
    delete_all_old_shadow_meetings()


@bp.cli.command("generate-private-key")
def generate_private_key():
    """CLI command to generate a new RSA private key for JWT signing."""
    from joserfc.jwk import RSAKey

    saved_private_pem_str = (
        current_app.config["PRIVATE_KEY"] if current_app.config["PRIVATE_KEY"] else None
    )
    if saved_private_pem_str:
        if (
            input(
                "A private-key has already been saved in the settings.\n"
                "If you choose to change the current private-key, "
                "all old tokens will become invalid.\n"
                "Are you sure you want to get a new private-key "
                "to copy in setting? (y/n) "
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
    """CLI command to generate JWT token for SIPMediaGW authentication."""
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
                    "iss": (
                        f"{current_app.config['PREFERRED_URL_SCHEME']}"
                        f"://{current_app.config['SERVER_NAME']}"
                    )
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
        except Exception as e:
            print(
                "Your private-key is invalid. "
                f"You must generate and save a new one. {e}"
            )


@bp.cli.command("check-sip-settings")
def check_sip_settings():
    """CLI command to validate SIPMediaGW configuration settings."""
    error_message = ""
    from joserfc.jwk import RSAKey

    saved_private_pem_str = (
        current_app.config["PRIVATE_KEY"] if current_app.config["PRIVATE_KEY"] else None
    )
    if not current_app.config["ENABLE_SIP"]:
        error_message += "You need to turn on ENABLE_SIP\n"
    if not current_app.config["FQDN_SIP_SERVER"]:
        error_message += "You need to save the FQDN_SIP_SERVER\n"
    if saved_private_pem_str is None:
        error_message += "You need to generate and save a private-key\n"
    try:
        key = RSAKey.import_key(saved_private_pem_str)
        if not key.is_private:
            error_message += (
                "Your private-key is invalid. You must generate and save a new one."
            )
    except Exception as e:
        error_message += (
            f"Your private-key is invalid. You must generate and save a new one. {e}"
        )
    print(error_message) if error_message else print("SIPMediaGW settings are OK.")


@bp.cli.command("check-sip-token")
@click.argument("token")
def check_sip_token(token):
    """CLI command to validate a JWT token against the configured private key."""
    from b3desk.utils import check_token_errors

    if not (errors := check_token_errors(token)):
        print("Token provided is validated by current private key.")
    else:
        print(errors)
        print("Token provided is not valid.")

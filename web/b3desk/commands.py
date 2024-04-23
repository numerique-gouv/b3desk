import click
from flask import Blueprint
from flask import current_app

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

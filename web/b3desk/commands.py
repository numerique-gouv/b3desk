import click
import requests
from flask import Blueprint
from flask import current_app

bp = Blueprint("commands", __name__, cli_group=None)


class TooManyUsers(Exception):
    """Exception raised if email returns more than one user.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="More than one user is using this email"):
        self.message = message
        super().__init__(self.message)


class NoUserFound(Exception):
    """Exception raised if email returns no user.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message="No user with this email was found"):
        self.message = message
        super().__init__(self.message)


@bp.cli.command("get-apps-id")
@click.argument("email")
def get_apps_id(email):
    try:
        token_response = requests.post(
            f"{current_app.config['SECONDARY_IDENTITY_PROVIDER_URI']}/auth/realms/{current_app.config['SECONDARY_IDENTITY_PROVIDER_REALM']}/protocol/openid-connect/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "client_credentials",
                "client_id": f"{current_app.config['SECONDARY_IDENTITY_PROVIDER_CLIENT_ID']}",
                "client_secret": f"{current_app.config['SECONDARY_IDENTITY_PROVIDER_CLIENT_SECRET']}",
            },
        )
        token_response.raise_for_status()
    except requests.exceptions.HTTPError as exception:
        current_app.logger.error(
            "Get token request error: %s, %s", exception, token_response.text
        )
        raise exception
    access_token = token_response.json()["access_token"]

    try:
        users_response = requests.get(
            f"{current_app.config['SECONDARY_IDENTITY_PROVIDER_URI']}/auth/admin/realms/{current_app.config['SECONDARY_IDENTITY_PROVIDER_REALM']}/users",
            headers={
                "Authorization": f"Bearer {access_token}",
                "cache-control": "no-cache",
            },
            params={"email": email},
        )
        users_response.raise_for_status()
    except requests.exceptions.HTTPError as exception:
        current_app.logger.error(
            "Get user from email request error: %s, %s", exception, users_response.text
        )
        raise exception
    found_users = users_response.json()
    if (user_count := len(found_users)) > 1:
        too_many_users_exception = TooManyUsers(
            f"There are {user_count} users with the email {email}"
        )
        current_app.logger.error(too_many_users_exception.message)
        raise too_many_users_exception
    elif user_count < 1:
        no_user_found_exception = NoUserFound(
            f"There are no users with the email {email}"
        )
        current_app.logger.error(no_user_found_exception.message)
        raise no_user_found_exception

    [user] = found_users
    return user["username"]

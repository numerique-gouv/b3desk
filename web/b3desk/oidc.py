from authlib.integrations.base_client import OAuthError
from authlib.integrations.flask_client import FlaskOAuth2App
from authlib.integrations.flask_client import OAuth
from authlib.oidc.core import UserInfo
from joserfc import jwt
from joserfc.errors import InvalidKeyIdError
from joserfc.jwk import KeySet


class OIDCClient(FlaskOAuth2App):
    """OpenID Connect client that can read signed userinfo responses."""

    # Remove when authlib supports signed UserInfo responses:
    # https://github.com/authlib/authlib/issues/941
    def userinfo(self, check_audience=True, **kwargs):
        """Fetch the user claims, returned either as JSON or as a signed JWT."""
        metadata = self.load_server_metadata()
        response = self.get(metadata["userinfo_endpoint"], **kwargs)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
        if content_type != "application/jwt":
            return UserInfo(response.json())

        algorithms = metadata.get("userinfo_signing_alg_values_supported")
        try:
            key_set = KeySet.import_key_set(self.fetch_jwk_set())
            token = jwt.decode(response.text, key_set, algorithms=algorithms)
        except InvalidKeyIdError:
            key_set = KeySet.import_key_set(self.fetch_jwk_set(force=True))
            token = jwt.decode(response.text, key_set, algorithms=algorithms)
        claims_options = {"iss": {"essential": True, "value": metadata["issuer"]}}
        if check_audience:
            claims_options["aud"] = {"essential": True, "value": self.client_id}
        jwt.JWTClaimsRegistry(leeway=120, **claims_options).validate(token.claims)
        return UserInfo(token.claims)


class OIDCOAuth(OAuth):
    oauth2_client_cls = OIDCClient


def fetch_userinfo(client, token):
    """Fetch the user claims from the userinfo endpoint, and check they match the ID token subject."""
    userinfo = client.userinfo(token=token)
    if userinfo.get("sub") != token["userinfo"].get("sub"):
        raise OAuthError(description="The userinfo and ID token subjects differ")
    return userinfo

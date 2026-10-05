import requests
from authlib.integrations.base_client import OAuthError
from authlib.integrations.flask_client import FlaskOAuth2App
from authlib.integrations.flask_client import OAuth
from authlib.oidc.core import UserInfo
from joserfc import jwt
from joserfc.errors import InvalidKeyIdError
from joserfc.errors import JoseError
from joserfc.jwk import KeySet


class OIDCClient(FlaskOAuth2App):
    """OpenID Connect client that reads the user claims from the userinfo endpoint."""

    def authorize_access_token(self, **kwargs):
        """Fetch the access token, then the user claims from the userinfo endpoint."""
        token = super().authorize_access_token(**kwargs)
        try:
            userinfo = self.userinfo(token=token)
        except (requests.RequestException, JoseError) as exc:
            raise OAuthError(
                description=f"Could not fetch the userinfo: {exc}"
            ) from exc

        if userinfo.get("sub") != token["userinfo"].get("sub"):
            raise OAuthError(description="The userinfo and ID token subjects differ")

        token["userinfo"] = userinfo
        return token

    # Remove when authlib supports signed UserInfo responses:
    # https://github.com/authlib/authlib/issues/941
    def userinfo(self, **kwargs):
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
        jwt.JWTClaimsRegistry(
            leeway=120,
            iss={"essential": True, "value": metadata["issuer"]},
            aud={"essential": True, "value": self.client_id},
        ).validate(token.claims)
        return UserInfo(token.claims)


class OIDCOAuth(OAuth):
    oauth2_client_cls = OIDCClient

### Configuration

- migration from flask_pyoidc to authlib ({pr}`429`, {issue}`202` et {user}`SbirLobo`)

Les paramètres suivants sont supprimés :

- OIDC_ID_TOKEN_COOKIE_SECURE
- OIDC_REQUIRE_VERIFIED_EMAIL
- OIDC_USER_INFO_ENABLED
- OIDC_OPENID_REALM
- OIDC_USERINFO_HTTP_METHOD
- OIDC_AUTH_URI
- OIDC_USERINFO_URI
- OIDC_TOKEN_URI
- OIDC_INTROSPECTION_AUTH_METHOD
- OIDC_REDIRECT_URI
- OIDC_SERVICE_NAME
- OIDC_ATTENDEE_INTROSPECTION_AUTH_METHOD
- OIDC_ATTENDEE_USERINFO_HTTP_METHOD

`OIDC_ATTENDEE_SERVICE_NAME` ne prend plus la valeur de `OIDC_SERVICE_NAME` par défaut. Il faut le renseigner pour afficher le nom du service d’authentification dans la modale d’invitation.

Les ID tokens et les réponses *userinfo* signés en HS256, HS384 ou HS512 ne sont plus pris en charge. Le client doit être enregistré avec un algorithme asymétrique, par exemple RS256 ou ES256.

L’URL de retour des fournisseurs d’identité ne se configure plus avec `OIDC_REDIRECT_URI`.
Elle est construite à partir de `PREFERRED_URL_SCHEME` et `SERVER_NAME` : `https://<SERVER_NAME>/oidc_callback`.

### Modifié

- Lorsque le jeton est expiré, l'API retourne des codes d'erreur HTTP 401.
- Lorsque l'audience du jeton est incorrecte, l'API retourne des codes d'erreur 401.
- Lorsque le fournisseur d’identité ne peut pas vérifier le jeton, l’API retourne des codes d’erreur HTTP 503.
- La déconnexion ne termine plus la session des participants authentifiés auprès de leur fournisseur d’identité. Elle ne termine que celle des organisateurs.
- Le nom du cookie de session dépend de la version mineure de B3Desk, par exemple `session_1_8`. Les utilisateurs sont donc déconnectés à chaque mise à jour mineure. Il est configurable avec `SESSION_COOKIE_NAME`.

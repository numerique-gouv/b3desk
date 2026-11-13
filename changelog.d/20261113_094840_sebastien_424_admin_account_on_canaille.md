### Actions requises

- Les administrateurs ne sont plus des comptes B3Desk : ils se connectent avec un serveur d'identité qui leur est réservé, par exemple Canaille. Avant la mise à jour, déployez ce serveur, puis créez-y le client OIDC de B3Desk, le groupe des administrateurs et leurs comptes. Renseignez ensuite les paramètres `OIDC_ADMIN_*`. Sans cela, plus personne n'accède au backoffice. La procédure est décrite dans la section « Gestion des administrateurs » de la documentation des paramètres ({pr}`464`, {issue}`424` et {user}`SbirLobo`).

### Migrations

- [`4352286dd469`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/4352286dd469_exclude_admin_from_user.py) supprime la colonne `admin` de la table des utilisateurs ({pr}`464`, {issue}`424` et {user}`SbirLobo`).

### Configuration

- Nouveaux paramètres du serveur d'identité des administrateurs ({pr}`464`, {issue}`424` et {user}`SbirLobo`) :
  - `OIDC_ADMIN_ISSUER`, `OIDC_ADMIN_CLIENT_ID` et `OIDC_ADMIN_CLIENT_SECRET`, sans valeur par défaut. `OIDC_ADMIN_ISSUER` est obligatoire quand `OIDC_ADMIN_ENABLED` est activé : sinon B3Desk refuse de démarrer.
  - `OIDC_ADMIN_CLIENT_AUTH_METHOD`, qui vaut `client_secret_post` par défaut.
  - `OIDC_ADMIN_SCOPES`, qui doit contenir le scope `groups` pour que B3Desk reçoive les groupes du compte.
  - `OIDC_ADMIN_GROUP`, qui vaut `admin` par défaut : seuls les membres de ce groupe accèdent au backoffice.
  - `OIDC_ADMIN_SESSION_LIFETIME`, qui vaut `3600` secondes par défaut : c'est la durée de la session d'un administrateur.

### Modifié

- Les administrateurs se connectent sur `/admin/login`. Leur session est distincte de celle des utilisateurs : se connecter avec l'une ferme l'autre ({pr}`464`, {issue}`424` et {user}`SbirLobo`).
- La session d'un administrateur expire au bout de `OIDC_ADMIN_SESSION_LIFETIME` secondes après la connexion, même s'il est actif ({pr}`464`, {issue}`424` et {user}`SbirLobo`).
- La déconnexion d'un administrateur termine aussi sa session sur son serveur d'identité ({pr}`464`, {issue}`424` et {user}`SbirLobo`).
- Un administrateur ne peut ajouter à un salon que des documents par URL : il n'a pas de Nextcloud, et le téléversement lui est refusé ({pr}`464`, {issue}`424` et {user}`SbirLobo`).

### Supprimé

- Les commandes `flask user-to-admin` et `flask admin-to-user`, un user ne peut plus obtenir les droits admin ({pr}`464`, {issue}`424` et {user}`SbirLobo`).
- Le bouton « Admin » de l'en-tête ({pr}`464`, {issue}`424` et {user}`SbirLobo`).

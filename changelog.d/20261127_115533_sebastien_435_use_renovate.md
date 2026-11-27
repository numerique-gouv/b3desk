### Actions requises

- Installer https://github.com/apps/renovate sur le dépôt.
- La construction de l'image `web` télécharge désormais les dépendances front-end (DSFR, Remix Icon, Dropzone, CaptchEtat) depuis le registre npm et l'image `node` depuis Docker Hub : l'hôte qui construit l'image doit pouvoir y accéder ({pr}`469`, {issue}`435` et {user}`SbirLobo`).

### Ajouté

- Les dépendances Python, JavaScript, les images Docker, les GitHub Actions et les hooks pre-commit peuvent être mis à jour automatiquement par Renovate : les correctifs de sécurité (après 2 jours) et les versions correctives (après 7 jours) sont fusionnés automatiquement si l'intégration continue passe, les autres mises à jour font l'objet d'une pull request ({pr}`469`, {issue}`435` et {user}`SbirLobo`).

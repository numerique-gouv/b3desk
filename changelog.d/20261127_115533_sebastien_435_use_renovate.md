### Actions requises

- La construction de l'image `web` télécharge désormais les dépendances front-end (DSFR, Remix Icon, Dropzone, CaptchEtat) depuis le registre npm et l'image `node` depuis Docker Hub : l'hôte qui construit l'image doit pouvoir y accéder ({pr}`000`, {issue}`435` et {user}`SbirLobo`).
- Pour activer les mises à jour automatiques des dépendances, créer `renovate.env` à partir de `renovate.env.example`, y renseigner `RENOVATE_TOKEN` avec un token GitHub limité au dépôt et doté des [permissions requises par Renovate](https://docs.renovatebot.com/modules/platform/github/#running-using-a-fine-grained-token), puis ajouter une tâche cron sur l'hôte, comme décrit dans la section « Mise à jour automatique des dépendances » de la documentation de déploiement.

### Ajouté

- Les dépendances Python, JavaScript, les images Docker, les GitHub Actions et les hooks pre-commit peuvent être mis à jour automatiquement par Renovate, en auto-hébergé : les correctifs de sécurité (après 2 jours) et les versions correctives (après 7 jours) sont fusionnés automatiquement si l'intégration continue passe, les autres mises à jour font l'objet d'une pull request ({pr}`000`, {issue}`435` et {user}`SbirLobo`).

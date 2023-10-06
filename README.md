# B3Desk


Frontal OIDC de gestion simplifiée des visioconférences BigBlueButton.

[![Check coverage](https://github.com/numerique-gouv/b3desk/actions/workflows/Test_coverage.yml/badge.svg)](https://github.com/numerique-gouv/b3desk/actions/workflows/Test_coverage.yml) [![Check lint](https://github.com/numerique-gouv/b3desk/actions/workflows/Check_lint.yml/badge.svg)](https://github.com/numerique-gouv/b3desk/actions/workflows/Check_lint.yml) [![Check local run](https://github.com/numerique-gouv/b3desk/actions/workflows/Check_local_run.yml/badge.svg)](https://github.com/numerique-gouv/b3desk/actions/workflows/Check_local_run.yml)

B3Desk permet de créer et configurer des visioconférences et de garder ces configurations.

C'est une surcouche qui utilise BigBlueButton.

B3Desk permet donc de paramétrer les options offertes par BBB : le titre, le nombre de participants, les invitations, les autorisations, mais aussi de visionner les enregistrements de ces visio par exemple.

Son usage réside dans le fait que toute cette configuration est enregistrée et peut être réutilisée pour la prochaine visio.

## Déployer B3Desk en production avec Docker

Pour déployer uniquement l'application b3desk en production, seuls les conteneurs **web, broker, worker** sont requis, les autres peuvent être disponibles sur d'autres serveurs.

La commande ci-après permet de déployer en mode production ou préproduction :
```
docker compose -f docker-compose.yml -f docker-compose.prod.yml up
# ou
# docker compose -f docker-compose.yml -f docker-compose.preprod.yml up
```

## Installer B3Desk dans un environnement de développement local

Vous pouvez suivre la documentation dans [./CONTRIBUTING.md](./CONTRIBUTING.md) pour installer localement le projet et le tester.

## Publier une nouvelle version

- Mettre un tag sur le commit, portant le numéro de la version, avec `git tag vX.Y.Z`
- Pousser le commit ET le tag `git push origin main --tags`
- Se rendre sur [la page github de publication de version](https://github.com/numerique-gouv/b3desk/releases/new)
- Choisir le tag récemment ajouté, remplir les informations, publier la version.

Attention, pour que le numéro de version s'affiche correctement sur la version déployée,
il est nécessaire que le projet soit déployé avec git (c.à.d. qu'il y ait un dépôt git
qui soit déployé), et aussi que le commit qui soit déployé soit directement marqué par
un tag git. Dans les autres cas, c'est le numéro de commit qui sera affiché.

## Licence

Ce logiciel est mis à disposition sous la licence EUPL : https://commission.europa.eu/content/european-union-public-licence_fr

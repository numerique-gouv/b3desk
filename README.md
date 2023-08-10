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

## Licence

Ce logiciel est mis à disposition sous la licence EUPL : https://commission.europa.eu/content/european-union-public-licence_fr

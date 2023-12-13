# Déploiement

Pour déployer uniquement l'application b3desk en production, seuls les conteneurs **web, broker, worker** sont requis, les autres peuvent être disponibles sur d'autres serveurs.

La commande ci-après permet de déployer en mode production ou préproduction :
```
docker compose -f docker-compose.yml -f docker-compose.prod.yml up
# ou
# docker compose -f docker-compose.yml -f docker-compose.preprod.yml up
```

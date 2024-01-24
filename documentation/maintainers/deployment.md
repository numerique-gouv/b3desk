# Déploiement

Pour déployer uniquement l'application b3desk en production, seuls les conteneurs **web, broker, worker** sont requis, les autres peuvent être disponibles sur d'autres serveurs.

La commande ci-après permet de déployer en mode production ou préproduction :
```
docker compose -f docker-compose.yml -f docker-compose.prod.yml up
# ou
# docker compose -f docker-compose.yml -f docker-compose.preprod.yml up
```

Le fichier `run_webserver.sh` est lancé par le `Dockerfile` et migre la base de données. Ces docker-compose de prod et preprod peuvent donc être utilisés pour une primo-installation, ou sur une instance existante.

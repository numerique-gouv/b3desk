# Déploiement

## Branches et tags

Sur le [dépôt git](https://github.com/numerique-gouv/b3desk) les branches et tags suivants sont utilisés :

- `main` est la branche de développement.
  Elle sert à recevoir les PR de fonctionnalités et les corrections de bugs importantes.
  Elle est considérée non stable et ne doit pas être utilisée dans les envirorrements de production.
- `production` est la branche stable. Elle sert à recevoir les hotfixes.
  Elle est considérée stable et utilisable sur les environnements de production.
  Elle correspond toujours au dernier tag publié.
- Différents tags `vXX.YY.ZZ` marquent les jalons du projet.
  Chaque tag est considéré stable et peut être utilisé sur les environnements de production.


## Téléchargement du code source

### Primo-installation

Pour récupérer le code source la premier fois, utiliser `git clone` :

```bash
git clone https://github.com/numerique-gouv/b3desk.git
git switch production
```

La commande `git clone` n’est à utiliser qu’une seule fois lors d’une primo-installation.
Les mise à jour du code se feront avec d’autres commandes git.

### Version stable

On peut utiliser `git checkout` pour passer sur une branche ou tag stable :

```bash
# pour charger la dernière version stable
git switch production
git pull origin production

# pour charger un jalon spécifique
git fetch origin --tags
git checkout v1.0.0
```

### Version de développement

Afin de valider des PR provenant de github, on peut charger du code instable pour pouvoir le tester ensuite. Dans les commandes suivantes remplacer `<ID>` par le numéro de la PR :

```bash
# Récupération de la PR
git fetch origin pull/<ID>/head:pr<ID>

# Changement vers la branche de la PR
git switch pr<ID>
```

Puis, si de nouvelles modifications ont été ajoutées à la PR on peut mettre à jour le code avec :

```bash
git switch pr<ID>
git pull origin pr<ID>
```

## Configuration

### B3Desk

La configuration se fait dans un fichier nommé `web.env`.
Lors d’une primo-installation, créer le fichier de configuration à partir de `web.env.example` :

```bash
cp web.env.example web.env
```

Adapter les valeurs du fichiers de configuration à partir des indications du chapitre sur la {ref}`Configuration de B3Desk<maintainers/settings:B3Desk>`.

### Serveur web

Paramétrer le chargement des pages d’erreurs statique sur le serveur web frontal à partir des indications du chapitre sur la {ref}`Configuration de Nginx<maintainers/settings:Nginx>`.

Faire attention à ne pas mettre en cache les pages dynamiques de B3Desk.

## Lancement des conteneurs

Enfin lorsque la bonne branche est chargée et que l’application est correctement configurée, on peut lancer les conteneurs avec les commandes suivantes :

```bash
# En production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up

# En pré-production
docker compose -f docker-compose.yml -f docker-compose.preprod.yml up
```

Le fichier `run_webserver.sh` est lancé par le `Dockerfile` et migre la base de données automatiquement. Ces docker-compose de production et preproduction peuvent donc être utilisés pour une primo-installation, ou sur une instance existante.

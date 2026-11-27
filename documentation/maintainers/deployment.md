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

Lorsqu'un conteneur B3Desk est en fonctionnement, la commande `flask config-dump` exporte la configuration courante dans un fichier au format `web.env`.
Chaque variable y est précédée de sa description.
Les variables que vous avez renseignées sont actives, les autres sont en commentaire avec leur valeur par défaut.
Les valeurs déduites d'autres variables, comme `OIDC_ATTENDEE_CLIENT_SECRET` ou `SESSION_COOKIE_SECURE`, restent en commentaire.
Le fichier peut donc servir de `web.env`.

```bash
# Exporte le fichier dans web/conf/web.env.dump sur l'hôte
docker exec web flask config-dump --output conf/web.env.dump
```

Sans l'option `--output`, le fichier `web.env.dump` est écrit dans le dossier de l'application, à l'intérieur du conteneur.
Ce dossier n'est pas monté sur l'hôte : le fichier disparaît quand le conteneur est recréé.

```{warning}
Le fichier exporté contient tous les secrets de la configuration en clair.
```

### Serveur web

Paramétrer le chargement des pages d’erreurs statique sur le serveur web frontal à partir des indications du chapitre sur la {ref}`Configuration de Nginx<maintainers/settings:Nginx>`.

Faire attention à ne pas mettre en cache les pages dynamiques de B3Desk.

## Lancement des conteneurs

Enfin lorsque la bonne branche est chargée et que l’application est correctement configurée, on peut lancer les conteneurs avec les commandes suivantes :

```bash
# En production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build

# En pré-production
docker compose -f docker-compose.yml -f docker-compose.preprod.yml up --build
```

L’option `--build` est nécessaire : le code de l’application est embarqué dans l’image et n’est plus monté depuis le dépôt. Sans reconstruction, un `git pull` ne change rien à ce qui s’exécute réellement dans les conteneurs.

Le fichier `run_webserver.sh` est lancé par le `Dockerfile` et migre la base de données automatiquement. Ces docker-compose de production et preproduction peuvent donc être utilisés pour une primo-installation, ou sur une instance existante.

## Mise à jour automatique des dépendances

[Renovate](https://docs.renovatebot.com/) ouvre des pull requests de mise à jour des dépendances Python, JavaScript, des images Docker, des GitHub Actions et des hooks pre-commit.
Il est auto-hébergé : le service `renovate` est décrit dans `docker-compose.renovate.yml`, et sa configuration dans `renovate.jsonc`.

Renovate lit `renovate.jsonc` sur la branche par défaut du dépôt GitHub, pas dans le dossier local.

### Configuration

Créer le fichier `renovate.env` à partir de `renovate.env.example` :

```bash
cp renovate.env.example renovate.env
```

Y renseigner `RENOVATE_TOKEN` avec un [token GitHub *fine-grained*](https://docs.github.com/fr/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#creating-a-fine-grained-personal-access-token) limité au seul dépôt `numerique-gouv/b3desk`, avec les permissions décrites dans la [documentation de Renovate](https://docs.renovatebot.com/modules/platform/github/#running-using-a-fine-grained-token).

```{warning}
`renovate.env` contient un secret : il est ignoré par git et ne doit jamais être commité.
```

Pour vérifier la validité de `renovate.jsonc` après une modification :

```bash
docker compose -f docker-compose.renovate.yml run --rm -w /repo renovate renovate-config-validator
```

### Lancement périodique

Renovate s'exécute puis s'arrête : il est lancé régulièrement par une tâche cron sur l'hôte.
Cron s'exécute depuis le dossier personnel de l'utilisateur : la commande doit d'abord se placer dans le dossier du dépôt.

Par exemple, pour un lancement tous les jours à 6 h, ajouter avec `crontab -e` :

```
0 6 * * * cd /chemin/vers/b3desk && docker compose -f docker-compose.renovate.yml run --rm renovate >> /var/log/renovate.log 2>&1
```

L'utilisateur de la crontab doit pouvoir lancer `docker` et écrire dans le fichier de log.

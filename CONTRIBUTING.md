# Contribuer à B3Desk

Bienvenue sur B3Desk, et merci de prendre le temps de vous intéresser à la contribution sur ce projet !

Vous trouverez ici les quelques indications qui permettront à B3Desk de grandir et de se développer que nous avons jugées intéressantes. N'hésitez pas à faire des suggestions !

## Lancer B3Desk localement

### Docker

Pour lancer l'application et coller au plus proche des conditions de production, un certain nombre de conteneurs doivent être lancés pour pouvoir s'assurer que l'ensemble reste fonctionnel. Les différents services sont dans les fichiers `docker-compose.yml` et `docker-compose.override.yml` qui vient surcharger le premier :
- web : le cœur de l'application, la surcouche à BigBlueButton qui permet de gérer les visioconférences
- keycloak : le service d'authentification avec un utilisateur `bbb-visio-user` instancié
- nextcloud : un des moyens disponibles pour partager des fichiers en visioconférence (persistance de l'installation dans `nextcloud/html`)
- postgres : la base de données qui va persister les données des services Nextcloud, keycloak et web (persistance des données dans `postgres/data`)
- worker : le worker celery permettant de gérer l'upload de fichiers de façon asynchrone
- broker : le broker redis qui maintient une liste de tâches dans laquelle vient se servir le worker
- tokenmock : un mock qui vient reproduire les conditions de prod de distribution d'un token pour la communication entre B3Desk et l'instance Nextcloud de l'utilisateur

Vous trouverez plus d'informations concernant la persistance des données pour certains de ces conteneurs dans {doc}`la documentation <dockerPersistence>`.

1. Configurer l'application web en créant le fichier `web.env` à partir du fichier `web.env.example`. Ce nouveau fichier est précisé dans `docker-compose.override.yml` qui vient surcharger le fichier `docker-compose.yml` lorsqu'aucun fichier n'est précisé dans la commande `docker compose`.
Pour que les liens vers le service BBB fonctionne, il est nécessaire de configurer les variables d'environnement BIGBLUEBUTTON_ENDPOINT et BIGBLUEBUTTON_SECRET.
**Si une seule variable d'environnement manque, toute ou partie de l'application dysfonctionne.** Si vous n'avez pas d'instance BBB à disposition, vous pouvez lancer votre propre instance localement en suivant le fichier `./bigbluebutton/Run-local-bbb.md`.

2. Démarrer l'application web, la base de données postgresql et le serveur d'authentification oidc keycloak préconfiguré avec docker-compose et attendre que les 3 soient prêts à accepter des connections (l'application web ne démarre pas correctement tant que les deux autres ne sont pas prêts et redémarre automatiquement jusqu'à ce qu'elle réussisse)

```bash
docker compose up  # ou docker-compose up
# docker compose down pour tout couper
```

3. Pour que l'authentification via le conteneur keycloak fonctionne depuis votre navigateur (cf https://stackoverflow.com/a/59579592) et pour que le conteneur Nextcloud soit accessible dans le réseau docker et requêtable depuis votre navigateur, vous devez ajouter les entrées suivantes dans votre fichier hosts (`/etc/hosts` sur une machine linux ou macOS) :

```
127.0.0.1 keycloak
127.0.0.1 nextcloud
```

4. Tester l'accès [http://localhost:5000] puis se connecter.
Le compte d'accès est `bbb-visio-user`, mot de passe `Pa55w0rd`.
Si nécessaire, tester l'accès au keycloak [http://localhost:8080] via l'interface d'administration. Le compte d'accès admin est `admin` (mot de passe unique dans les fichiers d'environnement).

### Environnement de développement

#### Installation locale
Installer localement le projet vous permettra de lancer black, ou bien les tests, sans avoir à utiliser de conteneur (Il est dans, tous les cas, **nécessaire** de faire tourner les conteneurs pour s'assurer que le tout reste fonctionnel).
L'installation locale peut être réalisé avec le Makefile situé à la racine du projet :
```bash
make install-dev
```
Utilisez ce Makefile comme référence pour vos commandes shell.

#### Poetry
L'environnement de développement est géré avec [Poetry](https://python-poetry.org/).

Installez l'environnement avec :
```bash
poetry install [--with GROUPE]
```

activez-le avec :
```bash
poetry shell
```

Si vous souhaitez ajouter des dépendances, utilisez également Poetry :
```bash
poetry add [--group GROUPE] PAQUET-PIP
```
vous devez ensuite impérativement mettre à jour les requirements de l'environnement modifié qui seront utilisées pour les conteneurs Docker de la production et de l'intégration continue :
```bash
make export-XXX-dependencies
```

## Soumettre des modifications

### Prérequis

#### Validité du code

Le nouveau code doit être testé. Pour lancer les tests, vous pouvez le faire dans un conteneur avec :
```bash
docker compose run --rm tests [pytest params]
```
ou bien dans l'environnement Poetry avec pytest (dont certains settings sont dans le fichier `pyproject.toml`) :
```bash
pytest
```

Pour tester le code sur les différentes versions de python en cours, et prévenir des incompatibilités avec des versions futures, utilisez :
```bash
tox
```

#### Conventions de code

Le code python doit suivre les conventions de la PEP 8. Dans les dépendance de développement du projet, on retrouve `flake8` et `black`.

Le code peut donc être formatté avec [black](https://pypi.org/project/black/) (dont certains settings sont dans le fichier `pyproject.toml`) :

```bash
black .
```

Vous pouvez également déléger cette tâche avec `pre-commit`.

Le paquet `pre-commit` est dans les dépendances de développement. Avec votre environnement activé, il vous suffit d'installer le hook git avec :
```
pre-commit install
```

Ainsi, lorsque vous ferez un commit, black sera automatiquement lancé et formatera le code si ça n'a pas été fait (il vous faudra ajouter ce nouveau changement avec git).

#### Intégration continue GitHub

GitHub Actions est utilisé afin de s'assurer que le code reste propre et fonctionnel et que les conteneurs peuvent communiquer entre eux pour s'assurer que l'embarquement de nouveaux développeur·euses sur de nouvelles machines est possible.

Cette intégration continue fait tourner des conteneurs Docker, les fichiers de requirements doivent donc être maintenus à jour.

La CI GitHub est utilisée pour :
- lancer les tests dans un environnement local (sans conteneur docker) : pour permettre aux développeurs d'être indépendant de docker sur leurs machines
- lancer les tests dans un conteneur : pour valider que l'app est iso dans un conteneur ou en local
- lancer tous les conteneurs et faire un healthcheck sur chacun : pour valider que la configuration locale est fonctionnelle, et notamment qu'un token bien généré permet à B3Desk de communiquer avec une instance Nextcloud
- valider que la couverture de test est au moins égale à la couverture précédente : pour inciter à ajouter des tests
- valider que le code a bien été formaté : un `black . --check` est lancé

### Pull requests

Les commit ne sont pas réalisés directement sur le dépot principal du projet. Pour contribuer, il est nécessaire de faire un [fork](https://help.github.com/articles/fork-a-repo/) et de proposer des pull request.

#### Workflow

Le projet est organisé de la façon suivante :

- Les modification sont faites sur une `branche` de votre **fork**.
- Lorsque le développement est prêt, une *pull request* vers la branche `main` du projet d'*origine* est réalisée
- Une fois ce {doc}`développement validé <../maintainers/codeReview>`, les mainteneurs du projet vont *merger* ces modifications sur `main`
- Lorsque suffisamment de modifications sont faites dans `main`, les mainteneurs peuvent décider de créer une nouvelle version du projet
- La branche `main` est *mergée* dans la branche `production`, référente pour les déploiements du projet B3Desk

#### Commits

Pour plus de cohérence dans le projet, les messages de commits, en anglais, doivent suivre les recommendations suivantes :

- décrire ce que **fait** le commit avec un verbe à l'impératif, du point de vue métier et non technique : "Display last meeting date to authentified user"
- ne pas hésiter à ajouter une *description* qui précise la justification métier, le pourquoi : "Meeting planner needs to remember when was last launched a meeting to update its title and the associated files"
- référencer les tickets si possible

### Cas particuliers

#### Migration des données

Flask-migrate est utilisé pour modifier le schéma de la base de données.
Pour générer un nouveau script de migration :

```
docker compose exec web flask db stamp head
docker compose exec web flask db migrate -m "nom de la migration"
docker compose exec web flask db upgrade
```

cf. https://flask-migrate.readthedocs.io/

En production, les migrations sont réalisées automatiquement par `run_webserver.sh`.

#### Traductions

Vous trouverez toutes les informations sur la traduction dans cette {doc}`documentation <translation>`.

## Mise en forme des pages

Le service utilise le style du [Système de Design de l'État (dsfr)](https://gouvfr.atlassian.net/wiki/spaces/DB/overview?homepageId=145359476)

## Liens utiles

- [docs.bigbluebutton.org/dev/api.html](https://docs.bigbluebutton.org/dev/api.html)
- [mconf.github.io/api-mate](https://mconf.github.io/api-mate/)

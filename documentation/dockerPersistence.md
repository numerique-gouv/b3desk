# Persister des données dans les conteneurs docker

Certaines données peuvent être persistées pour faciliter l'utilisation de l'environnement de développement.

La base de donnée PostgreSQL est le point central de chacun des services ayant besoin de sauvegarder des données.

Dans le `docker-compose-override.yml` qui va être utilisé dans l'environnement local de développement, on peut voir que le service `postgres` possède deux volumes :

- `docker-entrypoint-initdb.d` : les scripts et backups de base de donnée présent dans ce dossier vont être exécutés au lancement du conteneur si la ou les bases sont inexistantes.
- `/var/lib/postgresql/data` : ici on retrouvera toutes les données sauvegardées. En avoir fait un volume permet de les persister entre chacun des lancements du conteneur. Pour repartir de zéro, il suffit de supprimer le contenu du dossier `./postgres/data` (ainsi que `./nextcloud/html`, nous verrons plus tard pourquoi).

Les services ci-dessous persistent des données avec le conteneur postgres.

## keycloak

Le fichier `./postgres/initdb/keycloak.sql` contient les données de base nécéssaires à un usage local de l'app : un utilisateur `bbb-visio-user` ayant un mot de passe `Pa55w0rd`, ainsi qu'un administrateur (voir les variables d'environnement dans `./keycloak.env`)

Il est utilisé pour un projet vide, c'est pourquoi il est versionné.

## nextcloud

Le fichier `postgres/initdb/nextcloud.sh` permet de créer la base de donnée utilisable par le service `nextcloud`.

On retrouvera ensuite les fichiers Nextcloud dans le volume `/var/lib/postgresql/data` du service `postgres`.

Lorsque le projet vide est lancé, le programme d'installation de Nextcloud s'exécute. Nextcloud a donc besoin de cette base de données, mais aussi de vérifier qu'il n'a pas déjà été installé. Ce script vérifie l'existence de `/var/www/html/version.php` et s'il n'existe pas, installe Nextcloud dans ce dossier `/var/www/html`. C'est pourquoi le service `nextcloud` possède le volume `html` afin de garder un Nextcloud fonctionnel entre lancements de conteneurs.

Une bonne façon de désinstaller Nextcloud est donc de supprimer le contenu du dossier `./nextcloud/html`.

## postgres

La base postgres est également utilisée pour sauvegarder le métier de B3Desk, les meetings et leur récurrence entre autres.

Le fichier `./postgres/initdb/bbb-visio.sh` va permettre de créer la base de données requise pour B3Desk lors du premier lancement.

Par la suite, comme le service `postgres` a un volume sur `/var/lib/postgresql/data`, toutes les modifications entre lancements de conteneurs seront persistées pour un usage local. Pour supprimer ces données, il suffit à nouveau de vider le contenu du dossier `./postgres/data`.

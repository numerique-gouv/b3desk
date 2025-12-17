# Reproduire des conditions de production entre les services

Le `docker-compose.override.yml` permet de reproduire des conditions proches de la production en lançant tous les services requis et en permettant la communication entre chacun. ({doc}`voir ici <contributing>`).

Il reste cependant difficile de partager des fichiers depuis un nextcloud local vers une instance BigBlueButton.

En effet, les différents services communiquent localement entre eux grâce au réseau mis en place par Docker. l'application B3Desk est accessible localement sur b3desk.localhost:5000 et grâce à la configuration du `etc/host` la machine locale peut accéder avec un navigateur au keycloak sur `keycloak:8080` et au nextcloud sur `nextcloud:8000`.

La problématique que l'on rencontre sur le partage de fichier depuis Nextcloud par exemple pour le partage d'un second fichier qui va nécessairement passer par le worker Celery, est que l'url partagée par B3Desk pointe sur `b3desk.localhost:5000` qui est son domaine local. Or, lorsque le worker Celery communique cette url à une instance BigBlueButton, ce domaine ne va rien signifier pour lui, et le fichier ne sera pas téléchargé dans la visio.

Voilà un contournement possible pour le partage de fichiers via Nextcloud :

## Avoir un vrai domaine pour B3Desk

### Exposer le local sur un domaine

NGrok permet de rendre accessible un environnement local depuis un domaine temporaire.

Il suffit de l'installer, de créer un compte sur le service, de configurer votre authtoken comme précisé dans la [documentation](https://dashboard.ngrok.com/get-started/setup/linux).

Nous avons besoin de deux domaines, un pour B3Desk et un pour le Nextcloud.

Trouvez le fichier de configuration avec :
```
ngrok config check
```
Cette commande doit vous rendre le chemin de la config que vous pouvez alors éditer pour qu'elle contienne :
```
version: "xxxx"
authtoken: secret_token
tunnels:
  B3Desk:
    addr: 5000
    proto: http
  B3nc:
    addr: 80
    proto: http
```
Vous pouvez alors lancer la commande suivante pour obtenir deux domaines
```
ngrok start --all
```
Vous devriez voir apparaitre :
```
ngrok                                                                                                (Ctrl+C to quit)

Session Status                online
Account                       userxyz
[...]
Forwarding                    https://b3deskextdomain.ngrok-free.app -> http://localhost:5000
Forwarding                    https://nextcloudextdomain.ngrok-free.app -> http://localhost:80
```
Ainsi que le trafic sur ces url.

### Configurer B3Desk pour ce domaine

Pour que B3Desk soit fonctionnel sur l'url fournie par NGrok, il faut modifier la configuration du `web.env` :
```
SERVER_NAME=b3deskextdomain.ngrok-free.app
PREFERRED_URL_SCHEME=https
```

Attendez avant de relancer votre service, vous ne pouvez malheureusement pas encore vous authentifier depuis ce domaine.

## S'authentifier depuis un vrai domaine

### Avoir un OIDC fonctionnel

Maintenant que votre site dispose d'un vrai domaine, il faut encore qu'il puisse communiquer avec le Keycloak qui tourne localement et que celui-ci renvoie bien sur ce nouveau domaine.

Vous devez donc modifier à nouveau votre `web.env` avec :
```
OIDC_REDIRECT_URI=https://b3deskextdomain.ngrok-free.app/oidc_callback
```

Vous pouvez maintenant relancer votre service pour que cette configuration soit prise en compte :
```
docker compose up --build web keycloak -d
```
Si vous vous rendez maintenant sur `https://b3deskextdomain.ngrok-free.app` vous devriez arriver sur l'accueil du site.

### Configurer Keycloak

Il reste encore à configurer le Keycloak.

Rendez-vous sur `http://keycloak:8080` et connectez-vous en tant qu'admin.

Dans la partie 'Clients', cliquez sur le 'Client ID' de B3Desk pour pouvoir le modifier.

Ajoutez l'entrée `https://b3deskextdomain.ngrok-free.app/*` dans la liste de '* Valid Redirect URIs' et sauvegardez.

## Pouvoir acceder au Nextcloud depuis le domaine temporaire

### Accéder au Nextcloud depuis la nouvelle url

Pour pouvoir accéder au fichiers du Nextcloud depuis la page d'ajout de fichiers dans la visio, avec le bouton 'depuis le Nuage', il faut que la nouvelle url temporaire de Nextcloud `https://nextcloudextdomain.ngrok-free.app` soit dans la liste des `trusted_domains`.

Vous devez modifier la variable d'environnement :
```
NEXTCLOUD_TRUSTED_DOMAINS=nextcloudextdomain.ngrok-free.app
```

Et afin de pouvoir requêter Nextcloud depuis l'url de B3Desk, avec Filepicker, autorisé grâce au plugin WebAppPassword, il faut modifier `NEXTCLOUD_ALLOW_ORIGIN` qui se retrouvera dans le fichier de `config.php` de Nextcloud :

```
NEXTCLOUD_ALLOW_ORIGIN=https://b3deskextdomain.ngrok-free.app
```

Ces deux vaiables d'environnement sont dans le fichier `docker-compose.override.yml`. Il faut réinstaller Nextcloud en supprimant la base de données avec `sudo rm -rf nextcloud/html postgres/data` et en relançant les services :
```
docker compose up --build nextcloud -d
```

### Récupérer un token valide

Dans `docker-compose.override.yml` il faut modifier le `NC_HOST` du service `tokenmock` car `nextcloud` qui n'existe plus.

```
NC_HOST=https://nextcloudextdomain.ngrok-free.app`
```

Vous devez ensuite relancer ce service :
```
docker compose up --build tokenmock -d
```

### Autoriser le domaine de B3Desk à utiliser WebAppPassword

Dans les 'Paramètres d'administration' de Nextcloud (avec le compte admin), il faut ajouter le nouveau domaine de B3Desk `https://b3deskextdomain.ngrok-free.app` dans les 'Allowed origins' de WebAppPassword.

## Configuration terminée

Vous êtes maintenant capable de vous authentifier et de partager des fichiers depuis le Nextcloud local sur B3Desk, tout en surveillant les logs !

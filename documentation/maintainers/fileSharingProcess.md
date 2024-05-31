# Fonctionnement du partage de fichiers

Pour pouvoir partager des fichiers dans les salons BigBlueButton, l'instance doit être configurée d'une certaine manière.

Il existe trois façons de partager des fichiers dans la partie "Fichiers associés" d'un salon

## Par URL

Cette fonctionnalité est de base dans toutes les instances B3Desk.

Il suffit d'indiquer une url d'image valide au bon format et dans la limite de taille. Pas de configuration particulière, cette fonctionnalité devrait être utilisable tout le temps.

## Par le Nuage

Cette fonctionnalité nécessite un serveur webdav, plus précisément un Nextcloud.

### Authentification de l'utilisateur

#### Nextcloud

Pour que l'utilisateur B3Desk soit authentifié sur Nextcloud, le plugin [Nextcloud Sessiontoken](https://gitlab.octopuce.fr/octopuce-public/nextcloud-sessiontoken) doit être installé.

La documentation est assez explicite sur l'installation et l'utilisation de ce plugin.

Pour faire simple, une fois le plugin installé, il faut générer une paire de clé avec :

```
php hash-apikey.php
```

Cette commande va afficher une clé et un hash.

Le hash généré doit être ajouté au fichier `config/config.php` de l'instance Nextcloud :

```
<?php
$CONFIG = array (
    ...
    'sessiontoken_apikey_hash' => '<hash_généré_par_sessiontoken>',
);
```

La clé doit quant-à elle être utilisée par le service d'identité de Nextcloud.

#### Serveur d'identité

Ce serveur d'identité doit fournir le token de l'utilisateur.

Il va donc requêter l'url de l'instance Nextcloud, et plus précisément, une url mise à disposition par le plugin Nextcloud Sessiontoken, `/apps/sessiontoken/token` avec un POST et un body contenant la clé générée par Nextcloud Sessiontoken et l'utilisateur demandant le token :

```
{
    "apikey": "clé_générée_par_sessiontoken",
    "user": "identifiant_nextcloud_de_lutilisateur"
}
```

> Pour tester que Nextcloud peut répondre au serveur d'identité, on peut tester simplement la communication avec la commande suivante en ssh depuis ce serveur d'identité :
>
> `curl --location --request POST 'https://<url_nextcloud>/apps/sessiontoken/token' --header 'Content-Type: application/x-www-form-urlencoded' --data-urlencode 'apikey=<clé_générée_par_sessiontoken>' --data-urlencode 'user=<identifiant_nextcloud_de_lutilisateur>'`
>
> la réponse devrait-être la suivante :
> ```
> {
>     "token": "token-de-lutilisateur",
>     "loginName": "identifiant_nextcloud_de_lutilisateur",
>     "deviceToken": {
>         ...
>     }
> }
> ```

Le serveur d'identité va alors renvoyer cette information à B3Desk.

#### B3Desk

Pour récupérer le token d'identification de l'utilisateur auprès de Nextcloud, B3Desk va donc requêter ce serveur d'identité.

Afin de construire la requête, B3Desk a besoin des variables d'environnement suivantes :

- :attr:`~b3desk.settings.MainSettings.NC_LOGIN_API_URL`
- :attr:`~b3desk.settings.MainSettings.NC_LOGIN_API_KEY`

Il va donc requêter :attr:`~b3desk.settings.MainSettings.NC_LOGIN_API_URL` en POST avec un header "x-api-key" renseignant la variable :attr:`~b3desk.settings.MainSettings.NC_LOGIN_API_KEY` et un body contenant le username de l'utilisateur B3Desk :

```
{
    "username": "identifiant_de_lutilisateur"
}
```

> Pour tester que le serveur d'identité est capable d'interroger l'instance Nextcloud et de répondre avec le token utilisateur, on peut tester la communication entre B3Desk et ce serveur (et par la même occasion le Nextcloud) en ssh depuis le serveur B3Desk :
>
> `curl --location --request POST '<url_de_la_variable_NC_LOGIN_API_URL>' --header 'x-api-key: <NC_LOGIN_API_KEY>' --header 'Content-Type: application/json' --data-raw '{"username":"<identifiant_de_lutilisateur>"}'`
>
> la réponse devrait être au moins la suivante (si le `nc_login` est maquant dans la réponse, il sera ajouté par B3Desk) :
> ```
> {
>     "nctoken": "token-de-lutilisateur",
>     "nclocator": "url_nextcloud",
> }
> ```

##### Cas particulier : L'identifiant de l'utilisateur B3Desk n'est pas le même que l'identifiant Nextcloud

Dans le cas où l'identifiant d'un utilisateur donné sur B3Desk n'est pas le même que son identifiant sur l'instance Nextcloud, une étape supplémentaire est nécessaire pour retrouver l'identifiant correspondant.

B3Desk va donc requêter un autre serveur d'identité pour, à partir de l'email, retrouver l'identifiant Nextcloud de l'utilisateur. Il faut suivre la documentation {ref}`Jumelage avec Apps<maintainers/settings:Jumelage avec Apps>` pour bien configurer B3Desk et le serveur d'identité secondaire.

> Pour tester que B3Desk est bien capable de retrouver l'identifiant Nextcloud d'un utilisateur à partir de son mail, on peut exécuter la commande de cette documentation :
>
> ```
> docker exec -it <id_du_conteneur_B3Desk> flask get-apps-id <email_de_lutilisateur@mail.fr>
> ```
>
> Cette commande devrait répondre `ID from secondary identity provider for email <email_de_lutilisateur@mail.fr>: <identifiant_nextcloud_de_lutilisateur>`

### Utilisation du Filepicker

L'utilisateur une fois authentifié par Nextcloud doit pouvoir sélectionner les fichiers de son compte Nextcloud.

Pour le moment, le filepicker envoie bien le token de l'utilisateur, mais la fenêtre de sélection sur B3Desk indique "Non connecté" car l'url de B3Desk n'est pas autorisée.

Pour cela, Nextcloud doit autoriser le Filepicker à retrouver ses fichiers et donc être configuré pour cela.

#### Nextcloud

Le plugin [WebAppPassword](https://apps.nextcloud.com/apps/webapppassword) doit être installé sur le Nextcloud.

Une fois installé, pour autoriser le Filepicker à retrouver les fichiers, il faut autoriser les requêtes provenant de l'url de B3Desk. Il faut donc l'ajouter dans le fichier `config/config.php` :

```
<?php
$CONFIG = array (
    ...
    'webapppassword.origins' => '<url_de_B3Desk>',
);
```

Ou bien l'ajouter depuis l'interface d'administration du plugin WebAppPassword de Nextcloud, dans le champs "Allowed origins for webdav".

Après cette modification, les utilisateurs devraient pouvoir retrouver leurs fichiers Nextcloud et les ajouter à leur salon.

## Par Téléversement

Le téléversement utilise également la connexion Nextcloud. les fichiers ajoutés se retrouvent dans un dossier "visio-agents" à la racine du Nextcloud de l'utilisateur.

La documentation {ref}`Authentification de l'utilisateur<maintainers/fileSharingProcess:Par le Nuage:Authentification de l'utilisateur>` ci-dessus est donc à suivre.

La configuration d'un WebAppPassword n'est ici pas nécessaire car il n'y a pas d'interaction directe avec le Nextcloud. Le fichier est téléversé dans Nextcloud et il sera récupéré par la suite par BBB.

## Plusieurs fichiers dans le même salon

Lorsque plusieurs fichiers doivent être partagés dans un salon, le processus change légèrement.

Le premier fichier, celui qui sera affiché en diaporama à l'arrivée dans BigBlueButton, est envoyé directement dans la requête de création du salon, ou plus exactement, l'url que doit requêter BBB pour retrouver ce fichier est envoyée dans la requête de création de salon que fait B3Desk à BBB.

Les url des fichiers suivants sont envoyées de façon asynchrone au travers d'un worker Celery qui va communiquer les autres url à BBB.

Il faut donc s'assurer que le système broker-worker est fonctionnel et est bien capable de fournir les autres url à BigBlueButton.

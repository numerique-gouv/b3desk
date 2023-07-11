# Associer un fichier à un salon BBB dans B3desk

Il est possible d'associer un fichier à un salon
## Association des fichiers avant le lancement du salon

L'association des fichiers avant le lancement se fait via l'URL formattée
https://B3DESK/meeting/files/MEETINGID
Si la connexion Nextcloud est fonctionnelle, 3 boutons s'affichent, sinon, seulement l'association par URL s'affiche.

### Nextcloud
L'association par Nextcloud se fait grâce aux donnéees user.nc_login, user.nc_token et user.nc_locator pour avoir une connexion webdav.
Un client webdav est initié et, une fois les fichiers sélectionnés, permet de lister et récupérer le chemin complet d'accès au fichier, stocké dans meeting_files.nc_path.

### URL
L'association par URL est simpliste et consiste en l'écriture de l'URL directement dans la table meeting_files.url.

### Téléversement
L'association par téléversement se fait en cliquer-glisser grâce au module JS 'dropzone', disponible localement et versionné dans le code source, ce fichier est donc une dépendance qu'il faut penser à mettre à jour régulièrement.
Une fois le fichier déposé, l'upload commence, et se fait par morceaux ( chunk ).
Le fichier est reconstitué sur le serveur B3desk dans le dossier renseigné à la variable d'environnement TMP_UPLOAD ( disponible dans web.env ).

Une fois le fichier entièrement reçu, le client WEBDAV ( connecté à Nextcloud donc ) réenvoie ce fichier dans le Nextcloud, dans le dossier créé à la racine de la connexion, nommé visio-agent.
Lorsque le téléversement se déroule sans accroc, le fichier stocké sur le serveur B3desk est ensuite supprimé.

**En revanche, pour les cas où l'upload pose un problème quelconque, on se retrouve avec un dossier qui ne fait 'que' grossir, il faut donc le purger régulièrement.**
Actuellement, un cron d'exemple est proposé : web/misc/delete_uploaded_files.cron.

### Gestion de l'identité

La récupération des éléments de connexion à Nextcloud se fait comme suit :

1. la personne arrive sur B3desk
2. la personne se connecte via le keycloak
3. par le keycloak, B3desk reçoit l'information 'preferred_username', qui **FAIT LE LIEN D'IDENTITÉ AVEC LE LOGIN NEXTCLOUD**
4. B3desk fait ensuite une requête aux variable d'environnement NC_LOGIN_API_URL avec la clé NC_LOGIN_API_KEY. L'équivalent dans l'environnement de développement local est le service 'tokenmock'.
5. L'appli 'tokenmock', elle, lance à son tour une requête au nextcloud associé au 'preferred_username' qu'on lui demande (dans le code actuel, tout est envoyé vers le même docker, mais l'appli 'tokenmock', en étant entre B3desk et Nextcloud, permet d'avoir XXX instances nextcloud derrière elle)
6. L'instance Nextcloud associée au 'preferred_username' demandé reçoit une requête HTTP sur l'url '/apps/sessiontoken/token' ( ou un endpoint qui appelle l'appli 'sessiontoken' ).
7. L'appli sessiontoken crée un token d'accès et les infos redescendent jusqu'à B3desk.

Pour vérifier que la communication entre chacun des conteneurs fonctionne correctement, vous pouvez suivre les étapes suivantes :

#### Vérifier que Nextcloud renvoie des autorisations

- se connecter sur le service `tokenmock` avec `docker exec -it id /bin/bash`
- faire un appel vers le service Nextcloud en passant par le session token et en indiquant l'utilisateur concerné (comme le `bbb-visio-user` par exemple) :
```
curl -X POST $NC_HOST/apps/sessiontoken/token -d "apikey=$NEXTCLOUD_SESSIONTOKEN_KEY&user=relevant-b3desk-username&name=device_name"
```
- le conteneur Nextcloud devrait répondre :
```
{"token":"XXxxX-XxXxx","loginName":"relevant-b3desk-username","deviceToken":{"id":x,"name":"device_name","lastActivity":x,"type":x,"scope":{"filesystem":true}}}
```

#### Vérifier que B3Desk peut demander des autorisation via le service `tokenmock` :

- en local, faire un appel vers le service `tokenmock` en indiquant l'utilisateur concerné (comme le `bbb-visio-user` par exemple) :
```
curl -X POST localhost:9000/index.php -H "x-api-key: $NC_LOGIN_API_KEY" -H 'Content-Type: application/json' -d '{"username":"relevant-b3desk-username"}'
```
- le service `tokenmock` devrait répondre :
```
{"nctoken":"xXxxX-XXXxx","nclocator":"http:\/\/nextcloud","nclogin":"relevant-b3desk-username"}
```
- si ça n'est pas le cas, essayez de vous connecter sur le service `tokenmock` et lancez le curl sur `localhost` sans port. Le service doit être capable de générer un token.

## Association des fichiers lors du lancement du salon

Une fois les fichiers associés au salon, la personne peut décider de démarrer sa visioconférence.
Il se déroule alors la chose suivante :

1. si le salon est déjà ouvert, la personne est juste redirigée vers le salon en cours
2. si le salon doit être créé, il est créé ( eh ouais ), il se passe alors 2 choses au niveau des fichiers associés
  - Le fichier noté comme étant celui par défaut est DIRECTEMENT associé au salon, via un fichier XML inséré dans l'appel API 'create' ( doc de référence : https://docs.bigbluebutton.org/development/api#pre-upload-slides )
  - Les autres fichiers sont poussés dans une job queue via celery ( qui communique avec B3desk via redis ). Une requête au BBB va ensuite être lancée sur l'endpoint insertDocument ( doc de référence : https://docs.bigbluebutton.org/development/api#insertdocument )

 Le résultat obtenu est une association des fichiers fonctionnelle, un salon qui se lance rapidement, et des fichiers 'secondaires' qui s'uploadent ensuite en background sans bloquer le déroulé du cours. Des notifications dans le salon apparaissent à chaque ajout de fichier.

**Troubleshooting : Si la création du salon part en timeout, il y a probablement un problème de communication entre B3desk et Celery et Redis, bien vérifier les variables d'environnement correspondantes**

## Association des fichiers en cours de visio dans un salon

Une fois le salon lancé et le cours en cours ( eh ouais ), il est encore possible d'associer des fichiers depuis nextcloud.
Les infos pour cela sont passées lors de la création du salon, via les paramètres `presentationUploadExternalUrl` et `presentationUploadExternalDescription`
( doc de référence : https://docs.bigbluebutton.org/development/api#upload-slides-from-external-application-to-a-live-bigbluebutton-session ).
L'URL fournie en l'occurence pour B3desk est /meeting/files/<meeting_id>/insertDocuments
La description fournie est modifiable via la var d'env "EXTERNAL_UPLOAD_DESCRIPTION" dans le fichier web.env

**Remarque : sur l'interface d'ajout de fichiers par l'extérieur, la personne qui s'y rend doit avoir une connexion Nextcloud valide.**

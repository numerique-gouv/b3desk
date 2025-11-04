# Instance locale de BigBlueButton

Si vous n'avez pas accès à une instance BBB pour exécuter B3Desk et la tester, vous pouvez lancer un conteneur BBB.

Voici les étapes à suivre pour avoir un conteneur BBB local correctement configuré.

## Étapes d'installation

Il existe un [script officiel](https://github.com/bigbluebutton/docker-dev) pour construire l'image Docker de BBB.
Il a été copié dans `bigbluebutton/create_bbb.sh`.

### Créer le conteneur BBB

```bash
./bigbluebutton/create_bbb.sh --image=imdt/bigbluebutton:3.0.x-develop --update bbb30
```
L'image est assez volumineuse (~8Go), il faudra donc être patient.

- Le script devrait afficher l'url et le secret du service BBB.
```
    URL: https://bbb30.test/bigbluebutton/
    Secret: unknownBbbSecretKey

    Link to the API-Mate:
    https://bbb30.test/api-mate/#server=https://bbb30.test/bigbluebutton/&sharedSecret=bbbSecretKey

```
Cette commande vous montre également comment accéder au BBB API-Mate.

- Copiez l'url BBB (BIGBLUEBUTTON_ENDPOINT) et ajoutez `api` à la fin, ainsi que la clé secrète (BIGBLUEBUTTON_SECRET) dans votre fichier web.env
- Lancez les conteneurs B3Desk
- Vous avez maintenant un réseau b3desk_default avec tous les services en cours d'exécution et un service BBB autonome
- Vous devez les connecter ensemble avec :

### Ajouter le conteneur BBB au réseau local

```bash
docker network connect b3desk_default bbb30
```

Vous pouvez vérifier si ces services sont effectivement connectés avec un curl depuis bbb30 vers un service B3Desk par exemple

### Autoriser les requêtes http avec BBB

BBB doit explicitement autoriser les requêtes http vers b3desk :

```bash
docker exec bbb30 sed -i '$ a insertDocumentSupportedProtocols=https,http' /etc/bigbluebutton/bbb-web.properties
docker exec bbb30 bbb-conf --restart
```

## Lancer un conteneur existant

Si vous avez déjà installé BBB et que le conteneur existe toujours, il n'est pas nécessaire de le réinstaller (le script `create_bbb.sh` supprime toute instance existante et recrée une version mise à jour).

Vous devez simplement connecter les services :
```
docker network connect b3desk_default bbb30
```

Et lancer le conteneur BBB :
```
docker start bbb30
```

Vous pouvez vérifier qu'il fonctionne effectivement avec :
```
docker ps -a
```

## Configurer l'enregistrement MP4

Pour configurer BBB afin qu'il traite les enregistrements en vidéo MP4, comme en production, vous devez effectuer une [intervention manuelle](https://docs.bigbluebutton.org/administration/customize/#install-additional-recording-processing-formats). Il s'agit d'un problème qui n'est [pas encore résolu](https://github.com/bigbluebutton/bigbluebutton/issues/12241).

- Ouvrir une session dans le conteneur :

```
ssh bbb30
```

- Installer le paquet bbb-playback-video :

```
sudo apt-get install bbb-playback-video
```

- Éditer le fichier `/usr/local/bigbluebutton/core/scripts/bigbluebutton.yml` :

```
sudo vim /usr/local/bigbluebutton/core/scripts/bigbluebutton.yml
```

- Ajouter le traitement et la publication vidéo dans le fichier :

```
steps:
  archive: "sanity"
  sanity: "captions"
  captions:
    - "process:presentation"
    - "process:video"
  "process:presentation": "publish:presentation"
  "process:video": "publish:video"
```

- Redémarrer la file d'attente de traitement des enregistrements

```
sudo systemctl restart bbb-rap-resque-worker.service
```

# Instance locale de BigBlueButton

Si vous n'avez pas accès à une instance BBB pour exécuter B3Desk et la tester, vous pouvez lancer un conteneur BBB.

Voici les étapes à suivre pour avoir un conteneur BBB local correctement configuré.

## Étapes d'installation

Il existe un [script officiel](https://github.com/bigbluebutton/docker-dev) pour construire l'image Docker de BBB.
Il est disponible `bigbluebutton/create_bbb.sh` après avoir lancé la commande `git submodule update --init`.

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

Le conteneur BBB tourne sur son propre réseau Docker, isolé de celui de B3Desk : il faut donc les relier. Plutôt que le réseau `b3desk_default` géré par Compose (recréé à chaque `docker compose down`/`up`, ce qui débranche BBB), on utilise un réseau externe dédié `bbb-shared` qui survit aux redémarrages.

### Créer le réseau partagé

Cette opération n'est à faire qu'une seule fois. Le réseau doit exister avant le lancement des conteneurs B3Desk :

```bash
docker network create bbb-shared
```

Les services `web` et `worker` y sont déjà rattachés dans `docker-compose.override.yml`, ils le rejoignent donc automatiquement à chaque `docker compose up`.

### Ajouter le conteneur BBB au réseau local

Connectez le conteneur BBB au réseau partagé en lui donnant comme alias le nom d'hôte présent dans `BIGBLUEBUTTON_ENDPOINT` (par défaut `bbb30.test`), afin que B3Desk puisse le résoudre :

```bash
docker network connect --alias bbb30.test bbb-shared bbb30
```

Le conteneur conserve cette connexion tant qu'il n'est pas recréé : un simple `docker start bbb30` la préserve, mais une réinstallation via `create_bbb.sh` impose de relancer cette commande.

Vous pouvez vérifier que les services communiquent avec un curl depuis bbb30 vers un service B3Desk, par exemple.

### Autoriser les requêtes http avec BBB

BBB doit explicitement autoriser les requêtes http vers b3desk, sans quoi les fichiers de présentation n'apparaîtront pas dans le salon :

```bash
docker exec bbb30 sed -i '$ a insertDocumentSupportedProtocols=https,http' /etc/bigbluebutton/bbb-web.properties
docker exec bbb30 bbb-conf --restart
```

## Lancer un conteneur existant

Si vous avez déjà installé BBB et que le conteneur existe toujours, il n'est pas nécessaire de le réinstaller (le script `create_bbb.sh` supprime toute instance existante et recrée une version mise à jour).

Démarrez le conteneur BBB :
```
docker start bbb30
```

S'il a été recréé depuis sa dernière connexion, rattachez-le au réseau partagé (étape inutile sinon, la connexion ayant été conservée) :
```
docker network connect --alias bbb30.test bbb-shared bbb30
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
    - "process:ai-summary"
  "process:presentation": "publish:presentation"
  "process:video": "publish:video"
  "process:ai-summary": "publish:ai-summary"
```

- Redémarrer la file d'attente de traitement des enregistrements

```
sudo systemctl restart bbb-rap-resque-worker.service
```

## Configurer la transcription IA

La transcription nécessite d'avoir livekit comme moteur audio (afin d'avoir des pistes séparées) et un ensemble de scripts pour extraire l'audio, envoyer les pistes à un modèle de transcription, récupérer les transcript puis les envoyer à un second modèle pour produire une synthèse.

L'installation est automatisée, disponible avec le script suivant, aussi disponible à [cette adresse](https://bigbluebutton.nyc3.digitaloceanspaces.com/install-bbb-record-ai-summary.sh). Le script installe la [version 0.1.15](https://github.com/bigbluebutton/bbb-record-ai-summary/releases/tag/v0.1.15) du paquet `bbb-record-ai-summary`.

Le script demandera des informations sur le service à utiliser (Albert ou OpenAI) ainsi que la clé d'API.

Après un enregistrement, le transcript ainsi que le résumé sont alors disponibles via l'endpoint `getRecordings` de l'API BBB.

Le prompt de résumé par défaut utilisé est :

```
Create a concise summary that includes:

1. Main topics discussed
2. Key decisions made
3. Action items (if any)
4. Important points raised

Detect the language of the transcript and write the entire summary in that same language.
Never translate or switch languages.

Keep the summary clear, professional, and under 500 words.
```

```{literalinclude} install-bbb-record-ai-summary.sh
:language: bash
:caption: Script d'installation
```

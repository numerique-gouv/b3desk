# Journal des modifications

Ce fichier recense les changements notables de B3Desk, du point de vue des
personnes qui l'utilisent et de celles qui l'administrent.

Les entrées sont produites par [scriv](https://scriv.readthedocs.io) à partir
des fragments déposés dans `changelog.d`, décrits dans le [guide de
contribution](https://github.com/numerique-gouv/b3desk/blob/main/CONTRIBUTING.md).

Les versions antérieures à la mise en place de ce fichier sont reprises telles
qu'elles avaient été publiées sur la
[page des releases GitHub](https://github.com/numerique-gouv/b3desk/releases),
avec leur hétérogénéité d'origine.

<!-- scriv-insert-here -->

<a id='changelog-1.7.0'></a>
## v1.7.0 — 2026-09-09

### Ajouts
- Augmentation du nombre de délégataires par défaut, amélioration des messages d'erreur sur l'interface délégataires by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/364
- Backoffice lot 1 by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/361
- Menu de sélection de langue by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/366
- Configuration de la callback BBB et envoi de mail lors de la disponibilité d'un enregistrement by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/354
- Correction de fautes de frappe dans la documentation by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/377
- Transcription IA by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/362
- Backoffice lot 2 by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/374
- Affichage du nom du salon sur la page d'attente et la page de connexion by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/382

### Nouvelles migrations
- Nouveau champs `admin` sur la table d'utilisateurs
- Nouvelle table `groupes`
- Nouveaux champs `ai_summary` et `meta_disable_recording_ai_summary` sur la table meetings

**Full Changelog**: https://github.com/numerique-gouv/b3desk/compare/v1.6.3...v1.7.0

<a id='changelog-1.6.3'></a>
## v1.6.3 — 2026-05-27

- Personnalisation des claims OIDC by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/360

**Full Changelog**: https://github.com/numerique-gouv/b3desk/compare/v1.6.2...v1.6.3

<a id='changelog-1.6.2'></a>
## v1.6.2 — 2026-05-27

- Rajout des salons délégués dans l'API by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/357

**Full Changelog**: https://github.com/numerique-gouv/b3desk/compare/v1.6.1...v1.6.2

<a id='changelog-1.6.1'></a>
## v1.6.1 — 2026-05-13

### Chore
- bump requests from 2.32.5 to 2.33.0
- bump cryptography from 46.0.5 to 46.0.6
- bump pygments from 2.19.2 to 2.20.0
- bump cryptography from 46.0.6 to 46.0.7
- bump uv from 0.9.26 to 0.11.6
- bump pytest from 9.0.2 to 9.0.3
- bump mako from 1.3.10 to 1.3.11
- bump authlib from 1.6.9 to 1.6.11
- bump python-dotenv from 1.2.1 to 1.2.2
- bump lxml from 6.0.2 to 6.1.0
- bump mako from 1.3.11 to 1.3.12
- bump urllib3 from 2.6.3 to 2.7.0

### Features
- Réparation du système de traductions by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/308
- Translations update from Hosted Weblate by @weblate in https://github.com/numerique-gouv/b3desk/pull/344

### Fix
- Améliorations sur l'interface de délégation de réunions by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/339

### New Contributors
- @weblate made their first contribution in https://github.com/numerique-gouv/b3desk/pull/344

**Full Changelog**: https://github.com/numerique-gouv/b3desk/compare/v1.6.0...v1.6.1

<a id='changelog-1.6.0'></a>
## v1.6.0 — 2026-03-24

- Délégation de permissions aux salons by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/241 (Issue #226 )

### MIGRATION
- is-favorite column in meeting table become an intermediate table : favorite
- new intermediate table in DB : Permission
- the previoius meeting favorites are saved and restore with the db migration
- [77f91494af65](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/77f91494af65_create_meeting_access_and_favorite_.py) Add `meeting_access` table and `favorite` table
- [9dd2b54b4b11](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/9dd2b54b4b11_rename_meeting_user_id_to_owner_id.py) change `user_id` in `owner_id`  from `meeting_files` table.

### ADDED
- new setting : `MAXIMUM_MEETING_DELEGATES`
- new page : `delegation.html`

### DEV
- Adds 5 users

**Full Changelog**: https://github.com/numerique-gouv/b3desk/compare/v1.5.8...v1.6.0

<a id='changelog-1.5.8'></a>
## v1.5.8 — 2026-03-24

### FEATURES
- Mise à jour des catalogues de traduction by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/307

### FIXES
- Affichage complet du logo sur les instances avec un nom très long by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/319
- Nom de participant éditable pour les utilisateurs connectés by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/318

**Full Changelog**: https://github.com/numerique-gouv/b3desk/compare/v1.5.7...v1.5.8

<a id='changelog-1.5.7'></a>
## v1.5.7 — 2026-02-11

### Perf
- Suppression des requêtes inutiles de la page d'accueil by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/300

**Full Changelog**: https://github.com/numerique-gouv/b3desk/compare/v1.5.6...v1.5.7

<a id='changelog-1.5.6'></a>
## v1.5.6 — 2026-02-11

### Fixes
- Correction du crash de la commande `get-apps-id` by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/284
- Correction de la mise en ligne de fichiers pour les utilisateurs dont l'identifiant contient un espace by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/295
- Les utilisateurs authentifiés ne sont plus obligés d'attendre si le salon est lancé by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/294

### Settings
- Le paramètre `BIGBLUEBUTTON_REQUEST_TIMEOUT` est exprimé en secondes by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/291

### Features
- Taille maximale sur les champs by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/293
- Enregistrement manuel pré-coché dans le formulaire de création meeting by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/302
- Ajout du numéro de téléphone et du PIN dans l'API shadow meeting by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/303

### Other
- chore(deps): bump cryptography from 46.0.3 to 46.0.5 by @dependabot[bot] in https://github.com/numerique-gouv/b3desk/pull/306

**Full Changelog**: https://github.com/numerique-gouv/b3desk/compare/v1.5.5...v1.5.6

<a id='changelog-1.5.5'></a>
## v1.5.5 — 2026-01-21

### Migrations
- [3bf32932f522](https://github.com/numerique-gouv/b3desk/blob/622a768585e9df29708fb35537430b3bca74f0ad/web/migrations/versions/3bf32932f522_meeting_files_owner_id.py) adds a `owner` column to meeting files. #242
- [a1b2c3d4e5f6](https://github.com/numerique-gouv/b3desk/blob/622a768585e9df29708fb35537430b3bca74f0ad/web/migrations/versions/a1b2c3d4e5f6_remove_is_default_from_meeting_files.py) removes the `is_default` column from meeting files. #242

### Features
  - Add the room's visio-code in the BBB welcome message by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/275
  - Optional contact link in the footer by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/249
  - BIGBLUEBUTTON_REQUEST_TIMEOUT configuration parameter by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/276
  - Dedicated logger for BBB requests by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/278

### Fixes
  - Fix the recordings page by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/246
  - Improve visio-code and voice-bridge generation performance by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/271
  - Open the correct accordion on meeting edit form errors by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/255
  - Fix middle-click paste for visio-codes by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/253
  - Fix error when uploading documents by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/234
  - Host the state webinar icon locally by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/272
  - Fixes on Nextcloud connection by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/242
  - Jinja syntax error to capitalize string by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/280

### Other
  - Run the testsuite with PostgreSQL and sqlite by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/229
  - Use Python 3.14 in the Docker images by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/240
  - Use uv in the Docker images by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/239
  - Update Nextcloud file picker to version 1.0.4 by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/279
  - Release documentation improvements by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/283
  - Remove user reference from invitation link URLs by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/257
  - Remove the email meeting feature by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/267

<a id='changelog-1.5.4'></a>
## v1.5.4 — 2025-12-17

### FEATURES

- Log BBB room creation responses. #263

<a id='changelog-1.5.3'></a>
## v1.5.3 — 2025-12-17

### FIXES

- Increase User.preferred_username length. #265

<a id='changelog-1.5.2'></a>
## v1.5.2 — 2025-11-25

### FEATURE
- #211  Upload de fichiers Nextcloud depuis l'interface de BBB #223

### MIGRATION
- remove `meeting_files_external` table

<a id='changelog-1.5.1'></a>
## v1.5.1 — 2025-11-25

No change with 1.5.0

<a id='changelog-1.5.0'></a>
## v1.5.0 — 2025-11-25

### FIXES
- fixes join mail meeting bug by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/196
- fixes bug with paste function in visio-code inputs by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/207
- deletes private-key from tests to improve security by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/210
- #164 Rafraîchissement des identifiants nextcloud en cas d'erreur WebDAV by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/218
- fixes settings validators to inform on invalid settings without crash the app by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/222
- Hotfix db and quick meeting by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/192

### FEATURES

- Support for Python 3.13 by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/193
- adds a test for quick meeting route by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/197
- #179 changes default record name adding time by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/201
- https://github.com/numerique-gouv/b3desk/issues/169#issuecomment-3249079108 doc: add configuration examples by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/206
- #167 Mise à jour du texte de l'encart RIE by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/212
- #191 adds created_at info in user table by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/204
- #217 Ouverture des meetings dans un nouvel onglet by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/225
- #182 #203 adds logs to follow the life of the meetings by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/200

### CHANGES
- #109 Ré-écriture de tokenmock en Python by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/198
- Migration de poetry à uv by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/209
- #169 Captcha pour les codes salon by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/199
- Abandon de Python 3.9 by @azmeuk in https://github.com/numerique-gouv/b3desk/pull/224
- #99 update default parameters in shadow meetings by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/220
- #183 increases time before refresh each attempt to join a meeting in wait page by @SbirLobo in https://github.com/numerique-gouv/b3desk/pull/219

**Full Changelog**: https://github.com/numerique-gouv/b3desk/compare/v1.4.1...v1.5.0

### Migrations
- new column in user : preferred_username
- new column in user : created_at
- column `visio_code` in meeting is now a string

### Settings update
- LOG_CONFIG
- PISTE_OAUTH_CLIENT_ID
- PISTE_OAUTH_CLIENT_SECRET
- CAPTCHETAT_API_URL
- PISTE_OAUTH_API_URL
- CAPTCHA_NUMBER_ATTEMPTS

<a id='changelog-1.4.1'></a>
## v1.4.1 — 2025-08-07

### update packages
- Alembic
- SQLAlchemy

### visio code in DB
new migration to standardize meeting table

### quick meeting
fixes quick meeting bug  : it should not be saved in DB

<a id='changelog-1.4.0'></a>
## v1.4.0 — 2025-07-18

### Voice bridge management

> PR #168
> Fixes #147

B3Desk is now in charge of managing PIN (or voiceBridge in BBB terms) generation for users to be able to join meetings by phone.
New migration to set `voiceBridge` unique and generate one for existing `Meeting`, and a new table to keep track of recently deleted `voiceBridge`.
Adds 2 new configuration variables:

- `BIGBLUEBUTTON_DIALNUMBER` phone number used in BBB or Scalelite config, for display purpose
- `ENABLE_PIN_MANAGEMENT` defaults to False, enable B3Desk to send PIN on meeting creation. Require `BIGBLUEBUTTON_DIALNUMBER` to work

### Shadow meeting

> PR #172
> Fixes #99

Each user has a "shadow meeting" that can be used by calendar plugins to quickly create a `Meeting`. The new `api/shadow-meeting` displays urls to join this meeting.
New cron deletes old unused shadow meetings.
New migration on `Meeting` adds `last_connection_utc_datetime` and `is_shadow` attributes.

### SIP connection

> PR #180
> Fixes #16

B3Desk provides an url for SIPMediaGW and secures access with a token, reachable on `/sip-connect/<visio-code>` only with an `Authorization` token in request header.
New migration adds unique attribute `visio_code` and generate one for existing `Meeting`.
New [commands](https://b3desk.readthedocs.io/fr/latest/maintainers/settings.html#id1) to help an check for private key / token installation.
New app dependency installed by docker: `joserfc`
Adds 3 new configuration variables:

- `ENABLE_SIP` default to False enable B3Desk to give SIPMediaGW_url in API and invitation modal. Require `FQDN_SIP_SERVER` to work.
- `FQDN_SIP_SERVER` is the SIP domain used to create the SIPMediaGW_url : `<visio_code>@<fqdn_serveur_SIP>`
- `PRIVATE_KEY` to register the private key generated by joserfc

### Visio-code for users

> PR #188
> References #169

New user interface for meeting connection.
Adds a new form for logged-in / logged-out users to join a meeting with its visio-code through a POST request.
Updates DSFR version.

<a id='changelog-1.3.1'></a>
## v1.3.1 — 2025-05-22

- fixes #174 : Fixes STATS_URL connection error that caused the interface to crash

- fixes Matomo integration

<a id='changelog-1.3.0'></a>
## v1.3.0 — 2025-04-02

- Classement des salons
  Migration `44cab47dbc9b` qui ajoute les colonnes `updated_at` `created_at` (la migration ajoute la date du jour si valeur inexistante) et `is_favorite`
  fixes #26
- Nouveaux styles sur la personnalisation de salons
  fixes #89
- Gérer les erreurs de connexion à BBB
  fixes #39
- Ajustements LaSuite
  fixes #148
- Questionnaire en fin de session configurable
  fixes #122
- Erreurs de connexion au serveur d'identité
  fixes #119
- Log d'erreur de réponse BBB
  fixes #166

<a id='changelog-1.2.20'></a>
## v1.2.20 — 2025-02-13

- mis à jour le nombre de participants pour un défaut à 350.

<a id='changelog-1.2.19'></a>
## v1.2.19 — 2025-02-05

- Corrige la volumétrie de requêtes sur les enregistrements vidéo.

<a id='changelog-1.2.18'></a>
## v1.2.18 — 2024-09-12

- Met à jour les CGU
- Ajoute un lien cliquable dans le message de bienvenue du salon

<a id='changelog-1.2.17'></a>
## v1.2.17 — 2024-08-23

- Ajuste l'intégration de LaSuite
- Corrige l'affichage des liens d'invitations
- Met à jour la présentation des liens de partage :
  - Nouvelle configuration `VIDEO_STREAMING_LINKS` pour afficher les services de diffusion sur lesquels télécharger les enregistrements :
    - Dans le cas d'une instance CV/visio-agents `VIDEO_STREAMING_LINKS='{"PodEduc": "https://podeduc.apps.education.fr/", "Tubes": "https://tubes.apps.education.fr/"}'`
    - Dans le cas d'une instance webinaire, ne doit pas être renseignée ou doit être vide.

<a id='changelog-1.2.16'></a>
## v1.2.16 — 2024-07-23

- Désactive l'upload de fichiers à la création de salons. L'upload asynchrone de tous les fichiers permet au salon d'être créé plus rapidement.

<a id='changelog-1.2.15'></a>
## v1.2.15 — 2024-07-23

- Adapte l'image de fond de LaSuite numérique à l'id du service dédié

<a id='changelog-1.2.14'></a>
## v1.2.14 — 2024-07-23

- Ajoute la homepage de LaSuite numérique grâce à la variable d'environnement `ENABLE_LASUITENUMERIQUE` avec un défaut sur `False`

<a id='changelog-1.2.13'></a>
## v1.2.13 — 2024-07-22

- Update donnees_personnelles.html by @klorydryk in https://github.com/numerique-gouv/b3desk/pull/138

### New Contributors
- @klorydryk made their first contribution in https://github.com/numerique-gouv/b3desk/pull/138

**Full Changelog**: https://github.com/numerique-gouv/b3desk/compare/v1.2.12...v1.2.13

<a id='changelog-1.2.12'></a>
## v1.2.12 — 2024-06-07

- Corrige l'envoi en double des fichiers non défaut dans le salon

<a id='changelog-1.2.11'></a>
## v1.2.11 — 2024-06-07

- Indique le protocole actuel dans les liens d'invitation
- Ajoute la possibilité de brancher un outil de surveillance
- Documente l'environnement de développement pour des interfaces https exposées sur le web
- Documente le processus et les interfaces pour le partage de fichiers
- Corrige le partage de fichier en production
  fixes #130

<a id='changelog-1.2.10'></a>
## v1.2.10 — 2024-05-16

- Corrige la génération de hash de visio avec une string du rôle traduite en anglais

<a id='changelog-1.2.9'></a>
## v1.2.9 — 2024-05-16

- Assurer la rétrocompatibilité avec différentes méthodes de génération de hash

<a id='changelog-1.2.8'></a>
## v1.2.8 — 2024-05-16

- Corrige la création des hash de visio pour rester compatible avec les anciens.

<a id='changelog-1.2.7'></a>
## v1.2.7 — 2024-05-15

- Corriger l'absence de `nclogin` pour certain serveurs d'identité

<a id='changelog-1.2.6'></a>
## v1.2.6 — 2024-04-30

- Ajouter la possibilité de se connecter à un serveur d'identité secondaire pour récupérer les ID Nextcloud spécifiques avec un email utilisateur
  - Pour utiliser cette fonctionnalité, il est nécessaire de configurer les paramètres `SECONDARY_IDENTITY_PROVIDER_ENABLED`, `SECONDARY_IDENTITY_PROVIDER_URI`, `SECONDARY_IDENTITY_PROVIDER_REALM`, `SECONDARY_IDENTITY_PROVIDER_CLIENT_ID` et `SECONDARY_IDENTITY_PROVIDER_CLIENT_SECRET`. Voir la [documentation](https://b3desk.readthedocs.io/fr/latest/maintainers/settings.html#jumelage-avec-apps).

<a id='changelog-1.2.5'></a>
## v1.2.5 — 2024-04-26

- Ajouter une configuration de log basique

<a id='changelog-1.2.4'></a>
## v1.2.4 — 2024-04-25

- Ajouter les logs info sur les serveurs gunicorn de production
- Mettre à jour les librairies de test

<a id='changelog-1.2.3'></a>
## v1.2.3 — 2024-04-24

- Ajouter de la [documentation](https://b3desk.readthedocs.io/fr/latest/developers/imitateProduction.html) sur la création d'un environnement local fonctionnel pour du partage de fichiers
- Ajouter des logs sur la cinématique de partage de documents

<a id='changelog-1.2.2'></a>
## v1.2.2 — 2024-04-22

- Mise à jour de librairies
- Ajout de logs sur l'API BBB et sur le worker
- Ajout d'un badge notifiant l'environnement actuel
- Correction du système de partage de fichiers #123

<a id='changelog-1.2.1'></a>
## v1.2.1 — 2024-04-05

- fix settings comma separated list of string parsing

<a id='changelog-1.2.0'></a>
## v1.2.0 — 2024-04-04

- Ajouter un script de suivi Matomo #54
- Ajouter "https://" à la récupération de l'url du Nuage depuis LaBoîte #48
- Liens urls modérateurs/participants facilement identifiables / ajouter dans les urls un "/guest/" pour le lien invité et un "/admin/" pour le lien modérateur #93
- Ajout de l'académie en paramètre dans la création de salon #80
- Parcours de suppression de salle #90
- Informations limite de conservation des enregistrements #98
- Forcer la casse des noms venant du SSO #47
- UX : Tableau de bord et choix entre réunion immédiate et permanente
  #75
- Pages d'erreur statiques #81
- Mauvaise page d'atterrissage au lancement d'une visio depuis B3Desk #77
- Soupçons de problème de charge #76
- Pas de création des tables lors d'une primo-installation #78
- Fournir un script SQL pour passer les anciennes bases en v1.1 pour la mise à jour #49
- Documenter les options de configuration #10

<a id='changelog-1.1.6'></a>
## v1.1.6 — 2024-03-19

- Rétroportage du correctif #117 du bug qui masquait l'affichage du pdf par défaut lorsque `FILE_SHARING` était activé

<a id='changelog-1.1.5'></a>
## v1.1.5 — 2024-03-14

- Corrige le plantage du alembic_helper lors de la recherche d'existence de table, notamment dans le cas des pertes de numéro de migrations de base de données.

<a id='changelog-1.1.4'></a>
## v1.1.4 — 2024-03-12

- Divers correctifs sur l'API meetings à destination des plugins pour Thunderbird et Outlook
- Le paramètre `OIDC_INTROSPECTION_AUTH_METHOD` peut être utilisé pour paramétrer la manière dont b3desk se connecte au point d'accès d'introspection du serveur d'identité

<a id='changelog-1.1.3'></a>
## v1.1.3 — 2024-01-26

Ajouts :

- Page d'erreur statique pour nginx #81

<a id='changelog-1.1.2'></a>
## v1.1.2 — 2023-12-08

Corrections

-  Correction additionnelle en rapport avec le crash de la dropzone #58 #64

<a id='changelog-1.1.1'></a>
## v1.1.1 — 2023-12-07

Corrections
- Correction du chemin de téléversement de fichiers des conférences #59
- Correction du helper de migration alembic pour le test d'existence des colonnes dans la base de données #49

<a id='changelog-1.1.0'></a>
## v1.1.0 — 2023-10-25

Ajouts
- Option pour désactiver l'authentification des participants #9 #11
- Lecture des variables `OIDC_SCOPES` et `OIDC_ATTENDEE_SCOPES` depuis
  l'environnement. #7
- Personnalisation de l'URL du sondage de satisfaction #12 #29
- Message d'attente à l'entrée d'un séminaire #13 #34
- Template personnalisé pour les erreurs 400 #27 #37
- Affichage du numéro de version en pied de page #25 #31 #45

Corrections
- Correction de la variable %%CONFNAME%% en description du séminaire
  #18 #19
- Couleur de l'indicateur de chargement #13 #40

<a id='changelog-1.0.2'></a>
## v1.0.2 — 2023-07-18

Now with a licence: EUPL.

<a id='changelog-1.0.0'></a>
## v1.0.0 — 2023-07-17

First commit of this public repository of the BBB fronted provided and used by the French Ministry of Education.

# Journal des modifications

Ce fichier recense les changements notables de B3Desk, du point de vue des
personnes qui l'utilisent et de celles qui l'administrent.

Les entrées sont produites par [scriv](https://scriv.readthedocs.io) à partir
des fragments déposés dans `changelog.d`, décrits dans le [guide de
contribution](https://github.com/numerique-gouv/b3desk/blob/main/CONTRIBUTING.md).

<!-- scriv-insert-here -->

<a id='changelog-1.7.0'></a>
## v1.7.0 — 2026-09-09

### Migrations

- [`791755877bb1`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/791755877bb1_adds_user_admin_flag.py) ajoute la colonne `admin` à la table des utilisateurs.
- [`fd08854f3582`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/fd08854f3582_disable_ai_summary_by_default.py) ajoute la colonne `meta_disable_recording_ai_summary` à la table des salons.
- [`a3a6e932b2ae`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/a3a6e932b2ae_add_group_table_and_ai_summary.py) crée les tables `group` et `group_member`, puis remplace `meta_disable_recording_ai_summary` par une colonne `ai_summary` dont le sens est inversé. Une instance qui vient de la version 1.6.3 traverse les deux migrations et ne conserve que `ai_summary`.

Une fois la mise à jour terminée, `flask db current` renvoie `a3a6e932b2ae`.

### Ajouté

- Transcription IA ({pr}`362`, {user}`azmeuk`).
- Backoffice, premier lot ({pr}`361`, {user}`SbirLobo`).
- Backoffice, second lot ({pr}`374`, {user}`SbirLobo`).
- Menu de sélection de langue ({pr}`366`, {user}`azmeuk`).
- Configuration de la callback BBB et envoi d'un courriel lorsqu'un enregistrement devient disponible ({pr}`354`, {user}`SbirLobo`).
- Affichage du nom du salon sur la page d'attente et la page de connexion ({pr}`382`, {user}`SbirLobo`).

### Modifié

- Augmentation du nombre de délégataires par défaut et amélioration des messages d'erreur de l'interface de délégation ({pr}`364`, {user}`SbirLobo`).

### Corrigé

- Fautes de frappe dans la documentation ({pr}`377`, {user}`SbirLobo`).

<a id='changelog-1.6.3'></a>
## v1.6.3 — 2026-05-27

### Ajouté

- Personnalisation des claims OIDC ({pr}`360`, {user}`azmeuk`).

<a id='changelog-1.6.2'></a>
## v1.6.2 — 2026-05-27

### Ajouté

- Les salons délégués apparaissent dans l'API ({pr}`357`, {user}`azmeuk`).

<a id='changelog-1.6.1'></a>
## v1.6.1 — 2026-05-13

### Modifié

- Mise à jour des catalogues de traduction depuis Hosted Weblate ({pr}`344`, {user}`weblate`).
- Améliorations sur l'interface de délégation de réunions ({pr}`339`, {user}`SbirLobo`).
- Mise à jour des dépendances Python.

### Corrigé

- Réparation du système de traductions ({pr}`308`, {user}`SbirLobo`).

<a id='changelog-1.6.0'></a>
## v1.6.0 — 2026-03-24

### Migrations

- [`77f91494af65`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/77f91494af65_create_meeting_access_and_favorite_.py) ajoute les tables `meeting_access` et `favorite`. La colonne `is_favorite` de la table des salons devient une table intermédiaire `favorite` ; les favoris existants sont conservés et restaurés par la migration.
- [`9dd2b54b4b11`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/9dd2b54b4b11_rename_meeting_user_id_to_owner_id.py) renomme `user_id` en `owner_id` dans la table `meeting_files`.

Une fois la mise à jour terminée, `flask db current` renvoie `9dd2b54b4b11`.

### Configuration

- Nouveau paramètre `MAXIMUM_MEETING_DELEGATES`.

### Ajouté

- Délégation de permissions aux salons, avec une nouvelle page `delegation.html` ({pr}`241`, {issue}`226`, {user}`SbirLobo`).

### Modifié

- L'environnement de développement fournit cinq comptes utilisateurs supplémentaires.

<a id='changelog-1.5.8'></a>
## v1.5.8 — 2026-03-24

### Ajouté

- Mise à jour des catalogues de traduction ({pr}`307`, {user}`SbirLobo`).

### Corrigé

- Affichage complet du logo sur les instances portant un nom très long ({pr}`319`, {user}`SbirLobo`).
- Nom de participant éditable pour les personnes connectées ({pr}`318`, {user}`SbirLobo`).

<a id='changelog-1.5.7'></a>
## v1.5.7 — 2026-02-11

### Modifié

- Suppression des requêtes inutiles de la page d'accueil ({pr}`300`, {user}`SbirLobo`).

<a id='changelog-1.5.6'></a>
## v1.5.6 — 2026-02-11

### Configuration

- Le paramètre `BIGBLUEBUTTON_REQUEST_TIMEOUT` est désormais exprimé en secondes ({pr}`291`, {user}`SbirLobo`).

### Ajouté

- Taille maximale sur les champs de saisie ({pr}`293`, {user}`SbirLobo`).
- Enregistrement manuel pré-coché dans le formulaire de création d'un salon ({pr}`302`, {user}`SbirLobo`).
- Numéro de téléphone et PIN dans l'API des salons fantômes ({pr}`303`, {user}`SbirLobo`).

### Modifié

- Mise à jour des dépendances Python ({pr}`306`).

### Corrigé

- Crash de la commande `get-apps-id` ({pr}`284`, {user}`SbirLobo`).
- Mise en ligne de fichiers pour les personnes dont l'identifiant contient un espace ({pr}`295`, {user}`azmeuk`).
- Les personnes authentifiées ne sont plus obligées d'attendre lorsque le salon est déjà lancé ({pr}`294`, {user}`SbirLobo`).

<a id='changelog-1.5.5'></a>
## v1.5.5 — 2026-01-21

### Migrations

- [`3bf32932f522`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/3bf32932f522_meeting_files_owner_id.py) ajoute une colonne `owner` aux fichiers de salon ({pr}`242`).
- [`a1b2c3d4e5f6`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/a1b2c3d4e5f6_remove_is_default_from_meeting_files.py) retire la colonne `is_default` des fichiers de salon ({pr}`242`).

Une fois la mise à jour terminée, `flask db current` renvoie `a1b2c3d4e5f6`.

### Ajouté

- Le code visio du salon apparaît dans le message d'accueil BBB ({pr}`275`, {user}`SbirLobo`).
- Lien de contact optionnel dans le pied de page ({pr}`249`, {user}`SbirLobo`).
- Paramètre de configuration `BIGBLUEBUTTON_REQUEST_TIMEOUT` ({pr}`276`, {user}`SbirLobo`).
- Journal dédié aux requêtes BBB ({pr}`278`, {user}`azmeuk`).

### Modifié

- La suite de tests s'exécute sur PostgreSQL et SQLite ({pr}`229`, {user}`azmeuk`).
- Les images Docker utilisent Python 3.14 ({pr}`240`, {user}`azmeuk`).
- Les images Docker utilisent uv ({pr}`239`, {user}`azmeuk`).
- Le sélecteur de fichiers Nextcloud passe en version 1.0.4 ({pr}`279`, {user}`SbirLobo`).
- La référence à l'utilisateur disparaît des URL des liens d'invitation ({pr}`257`, {user}`azmeuk`).
- Améliorations de la documentation de publication ({pr}`283`, {user}`SbirLobo`).

### Supprimé

- La fonctionnalité d'envoi de salon par courriel est retirée ({pr}`267`, {user}`azmeuk`).

### Corrigé

- Page des enregistrements ({pr}`246`, {user}`SbirLobo`).
- Performances de génération des codes visio et des ponts vocaux ({pr}`271`, {user}`azmeuk`).
- Ouverture du bon accordéon en cas d'erreur du formulaire d'édition d'un salon ({pr}`255`, {user}`SbirLobo`).
- Collage au clic du milieu pour les codes visio ({pr}`253`, {user}`SbirLobo`).
- Erreur lors de la mise en ligne de documents ({pr}`234`, {user}`SbirLobo`).
- L'icône du webinaire de l'État est désormais hébergée localement ({pr}`272`, {user}`SbirLobo`).
- Connexion à Nextcloud ({pr}`242`, {user}`azmeuk`).
- Erreur de syntaxe Jinja sur la mise en capitale d'une chaîne ({pr}`280`, {user}`SbirLobo`).

<a id='changelog-1.5.4'></a>
## v1.5.4 — 2025-12-17

### Ajouté

- Journalisation des réponses de création de salon BBB ({issue}`263`).

<a id='changelog-1.5.3'></a>
## v1.5.3 — 2025-12-17

### Migrations

- [`9a4ffc3a0f0d`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/9a4ffc3a0f0d_increase_email_and_preferred_username_.py) porte les colonnes `email` et `preferred_username` de la table des utilisateurs à 255 caractères ({pr}`265`).

Une fois la mise à jour terminée, `flask db current` renvoie `9a4ffc3a0f0d`.

### Corrigé

- Les adresses électroniques et les noms d'utilisateur les plus longs ne sont plus tronqués ({pr}`265`).

<a id='changelog-1.5.2'></a>
## v1.5.2 — 2025-11-25

### Migrations

- [`9869cacd37a4`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/9869cacd37a4_removes_meeting_files_external_table.py) supprime la table `meeting_files_external`.

Une fois la mise à jour terminée, `flask db current` renvoie `9869cacd37a4`.

### Ajouté

- Mise en ligne de fichiers Nextcloud depuis l'interface de BBB ({issue}`211`, {pr}`223`).

<a id='changelog-1.5.1'></a>
## v1.5.1 — 2025-11-25

Aucun changement par rapport à la version 1.5.0.

<a id='changelog-1.5.0'></a>
## v1.5.0 — 2025-11-25

### Migrations

- [`3c8b6c640fee`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/3c8b6c640fee_visio_code_length.py) convertit la colonne `visio_code` de la table des salons en chaîne de 50 caractères.
- [`454adc444042`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/454adc444042_adds_created_at_in_user.py) ajoute la colonne `created_at` à la table des utilisateurs ; les comptes existants reçoivent la date du 1er janvier 1900.
- [`f68adee062bf`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/f68adee062bf_user_preferred_username.py) ajoute la colonne `preferred_username` à la table des utilisateurs.

Une fois la mise à jour terminée, `flask db current` renvoie `f68adee062bf`.

### Configuration

- Nouveaux paramètres `LOG_CONFIG`, `PISTE_OAUTH_CLIENT_ID`, `PISTE_OAUTH_CLIENT_SECRET`, `CAPTCHETAT_API_URL`, `PISTE_OAUTH_API_URL` et `CAPTCHA_NUMBER_ATTEMPTS`.

### Ajouté

- Prise en charge de Python 3.13 ({pr}`193`, {user}`azmeuk`).
- L'heure est ajoutée au nom par défaut des enregistrements ({issue}`179`, {pr}`201`, {user}`SbirLobo`).
- Exemples de configuration dans la documentation ({pr}`206`, {user}`azmeuk`).
- Mise à jour du texte de l'encart RIE ({issue}`167`, {pr}`212`, {user}`azmeuk`).
- Information `created_at` dans la table des utilisateurs ({issue}`191`, {pr}`204`, {user}`SbirLobo`).
- Les salons s'ouvrent dans un nouvel onglet ({issue}`217`, {pr}`225`, {user}`azmeuk`).
- Journaux permettant de suivre le cycle de vie des salons ({issue}`182`, {issue}`203`, {pr}`200`, {user}`SbirLobo`).
- Test de la route de réunion immédiate ({pr}`197`, {user}`SbirLobo`).

### Modifié

- Captcha sur les codes salon ({issue}`169`, {pr}`199`, {user}`SbirLobo`).
- Paramètres par défaut des salons fantômes ({issue}`99`, {pr}`220`, {user}`SbirLobo`).
- Le délai entre deux tentatives de connexion à un salon depuis la page d'attente est allongé ({issue}`183`, {pr}`219`, {user}`SbirLobo`).
- Réécriture de tokenmock en Python ({issue}`109`, {pr}`198`, {user}`azmeuk`).
- Migration de poetry à uv ({pr}`209`, {user}`azmeuk`).

### Supprimé

- Abandon de la prise en charge de Python 3.9 ({pr}`224`, {user}`azmeuk`).

### Corrigé

- Envoi du courriel de participation à un salon ({pr}`196`, {user}`SbirLobo`).
- Collage dans les champs de code visio ({pr}`207`, {user}`SbirLobo`).
- Rafraîchissement des identifiants Nextcloud en cas d'erreur WebDAV ({issue}`164`, {pr}`218`, {user}`azmeuk`).
- Les validateurs de configuration signalent les paramètres invalides sans faire planter l'application ({pr}`222`, {user}`SbirLobo`).
- Base de données et réunion immédiate ({pr}`192`, {user}`SbirLobo`).

### Sécurité

- La clé privée est retirée des tests ({pr}`210`, {user}`SbirLobo`).

<a id='changelog-1.4.1'></a>
## v1.4.1 — 2025-08-07

### Modifié

- Mise à jour d'Alembic et de SQLAlchemy.

### Corrigé

- Une réunion immédiate n'est plus enregistrée en base de données.

<a id='changelog-1.4.0'></a>
## v1.4.0 — 2025-07-18

### Migrations

- [`c25342fd2428`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/c25342fd2428_voicebridge_managed_by_b3desk.py) rend la colonne `voiceBridge` de la table des salons unique et génère une valeur pour les salons existants. La nouvelle table `previous_voice_bridge` conserve la trace des `voiceBridge` récemment supprimés ({pr}`168`, {issue}`147`).
- [`2e95af7b75cf`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/2e95af7b75cf_adds_shadow_meeting.py) ajoute les colonnes `last_connection_utc_datetime` et `is_shadow` à la table des salons ({pr}`172`, {issue}`99`).
- [`0052f608f4b3`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/0052f608f4b3_adds_visio_code_in_meeting.py) ajoute la colonne `visio_code` à la table des salons, la rend unique et génère une valeur pour les salons existants ({pr}`180`, {issue}`16`).

Une fois la mise à jour terminée, `flask db current` renvoie `0052f608f4b3`.

### Configuration

- `BIGBLUEBUTTON_DIALNUMBER` : numéro de téléphone configuré dans BBB ou Scalelite, à des fins d'affichage.
- `ENABLE_PIN_MANAGEMENT` : `False` par défaut, permet à B3Desk d'envoyer le PIN à la création d'un salon. Nécessite `BIGBLUEBUTTON_DIALNUMBER`.
- `ENABLE_SIP` : `False` par défaut, permet à B3Desk de fournir l'URL SIPMediaGW dans l'API et dans la fenêtre d'invitation. Nécessite `FQDN_SIP_SERVER`.
- `FQDN_SIP_SERVER` : domaine SIP utilisé pour construire l'URL SIPMediaGW, sous la forme `<visio_code>@<fqdn_serveur_SIP>`.
- `PRIVATE_KEY` : clé privée générée par joserfc.

### Ajouté

- B3Desk prend en charge la génération des PIN, le `voiceBridge` au sens de BBB, pour permettre de rejoindre un salon par téléphone ({pr}`168`, {issue}`147`).
- Chaque utilisateur dispose d'un salon fantôme, utilisable par les greffons d'agenda pour créer rapidement un salon. La nouvelle route `api/shadow-meeting` expose les URL permettant de le rejoindre ({pr}`172`, {issue}`99`).
- B3Desk fournit une URL pour SIPMediaGW et en protège l'accès par un jeton, sur `/sip-connect/<visio-code>` avec un en-tête `Authorization`. De nouvelles [commandes](https://b3desk.readthedocs.io/fr/latest/maintainers/settings.html#id1) aident à vérifier l'installation de la clé privée et du jeton. Ajoute la dépendance `joserfc` ({pr}`180`, {issue}`16`).
- Nouveau formulaire permettant de rejoindre un salon par son code visio, en POST, que l'on soit connecté ou non ({pr}`188`, {issue}`169`).
- Une tâche planifiée supprime les salons fantômes inutilisés ({pr}`172`, {issue}`99`).

### Modifié

- Mise à jour de la version du DSFR ({pr}`188`).

<a id='changelog-1.3.1'></a>
## v1.3.1 — 2025-05-22

### Corrigé

- Erreur de connexion à `STATS_URL` qui faisait planter l'interface ({issue}`174`).
- Intégration de Matomo.

<a id='changelog-1.3.0'></a>
## v1.3.0 — 2025-04-02

### Migrations

- [`44cab47dbc9b`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/44cab47dbc9b_add_date_and_favorite_in_meeting_table.py) ajoute les colonnes `created_at`, `updated_at` et `is_favorite` à la table des salons ; les salons existants reçoivent la date du jour.

Une fois la mise à jour terminée, `flask db current` renvoie `44cab47dbc9b`.

### Ajouté

- Classement des salons ({issue}`26`).
- Nouveaux styles pour la personnalisation des salons ({issue}`89`).
- Questionnaire de fin de session configurable ({issue}`122`).
- Journalisation des réponses en erreur de BBB ({issue}`166`).

### Modifié

- Ajustements pour LaSuite ({issue}`148`).

### Corrigé

- Gestion des erreurs de connexion à BBB ({issue}`39`).
- Erreurs de connexion au serveur d'identité ({issue}`119`).

<a id='changelog-1.2.20'></a>
## v1.2.20 — 2025-02-13

### Configuration

- Le nombre de participants par défaut passe à 350.

<a id='changelog-1.2.19'></a>
## v1.2.19 — 2025-02-05

### Corrigé

- Volumétrie des requêtes portant sur les enregistrements vidéo.

<a id='changelog-1.2.18'></a>
## v1.2.18 — 2024-09-12

### Ajouté

- Lien cliquable dans le message de bienvenue du salon.

### Modifié

- Mise à jour des CGU.

<a id='changelog-1.2.17'></a>
## v1.2.17 — 2024-08-23

### Configuration

- Nouveau paramètre `VIDEO_STREAMING_LINKS`, qui affiche les services de diffusion depuis lesquels télécharger les enregistrements. Sur une instance CV ou visio-agents : `VIDEO_STREAMING_LINKS='{"PodEduc": "https://podeduc.apps.education.fr/", "Tubes": "https://tubes.apps.education.fr/"}'`. Sur une instance webinaire, le paramètre doit rester vide ou absent.

### Modifié

- Ajustement de l'intégration de LaSuite.
- Nouvelle présentation des liens de partage.

### Corrigé

- Affichage des liens d'invitation.

<a id='changelog-1.2.16'></a>
## v1.2.16 — 2024-07-23

### Modifié

- La mise en ligne de fichiers à la création d'un salon est désactivée : l'envoi asynchrone de tous les fichiers permet au salon d'être créé plus rapidement.

<a id='changelog-1.2.15'></a>
## v1.2.15 — 2024-07-23

### Modifié

- L'image de fond de LaSuite numérique s'adapte à l'identifiant du service concerné.

<a id='changelog-1.2.14'></a>
## v1.2.14 — 2024-07-23

### Configuration

- Nouveau paramètre `ENABLE_LASUITENUMERIQUE`, `False` par défaut, qui ajoute la page d'accueil de LaSuite numérique.

<a id='changelog-1.2.13'></a>
## v1.2.13 — 2024-07-22

### Modifié

- Mise à jour de la page des données personnelles ({pr}`138`, {user}`klorydryk`).

<a id='changelog-1.2.12'></a>
## v1.2.12 — 2024-06-07

### Corrigé

- Envoi en double des fichiers non défaut dans le salon.

<a id='changelog-1.2.11'></a>
## v1.2.11 — 2024-06-07

### Ajouté

- Possibilité de brancher un outil de surveillance.
- Documentation de l'environnement de développement pour des interfaces HTTPS exposées sur le web.
- Documentation du processus et des interfaces de partage de fichiers.

### Modifié

- Les liens d'invitation indiquent le protocole courant.

### Corrigé

- Partage de fichiers en production ({issue}`130`).

<a id='changelog-1.2.10'></a>
## v1.2.10 — 2024-05-16

### Corrigé

- Génération du hash de visio lorsque le rôle est traduit en anglais.

<a id='changelog-1.2.9'></a>
## v1.2.9 — 2024-05-16

### Corrigé

- Rétrocompatibilité avec les différentes méthodes de génération de hash.

<a id='changelog-1.2.8'></a>
## v1.2.8 — 2024-05-16

### Corrigé

- Création des hash de visio, qui restent compatibles avec les anciens.

<a id='changelog-1.2.7'></a>
## v1.2.7 — 2024-05-15

### Corrigé

- Absence de `nclogin` sur certains serveurs d'identité.

<a id='changelog-1.2.6'></a>
## v1.2.6 — 2024-04-30

### Configuration

- Nouveaux paramètres `SECONDARY_IDENTITY_PROVIDER_ENABLED`, `SECONDARY_IDENTITY_PROVIDER_URI`, `SECONDARY_IDENTITY_PROVIDER_REALM`, `SECONDARY_IDENTITY_PROVIDER_CLIENT_ID` et `SECONDARY_IDENTITY_PROVIDER_CLIENT_SECRET`, décrits dans la [documentation](https://b3desk.readthedocs.io/fr/latest/maintainers/settings.html#jumelage-avec-apps).

### Ajouté

- Connexion à un serveur d'identité secondaire, pour récupérer les identifiants Nextcloud propres à un utilisateur à partir de son adresse électronique.

<a id='changelog-1.2.5'></a>
## v1.2.5 — 2024-04-26

### Ajouté

- Configuration de journalisation de base.

<a id='changelog-1.2.4'></a>
## v1.2.4 — 2024-04-25

### Ajouté

- Journaux de niveau info sur les serveurs gunicorn de production.

### Modifié

- Mise à jour des bibliothèques de test.

<a id='changelog-1.2.3'></a>
## v1.2.3 — 2024-04-24

### Ajouté

- [Documentation](https://b3desk.readthedocs.io/fr/latest/developers/imitateProduction.html) sur la mise en place d'un environnement local fonctionnel pour le partage de fichiers.
- Journaux sur la cinématique de partage de documents.

<a id='changelog-1.2.2'></a>
## v1.2.2 — 2024-04-22

### Ajouté

- Journaux sur l'API BBB et sur le worker.
- Badge signalant l'environnement courant.

### Modifié

- Mise à jour de bibliothèques.

### Corrigé

- Système de partage de fichiers ({issue}`123`).

<a id='changelog-1.2.1'></a>
## v1.2.1 — 2024-04-05

### Corrigé

- Lecture des paramètres exprimés sous forme de listes de chaînes séparées par des virgules.

<a id='changelog-1.2.0'></a>
## v1.2.0 — 2024-04-04

### Actions requises

- Lancer le script SQL fourni pour faire passer les anciennes bases en version 1.1 ({issue}`49`).

### Ajouté

- Script de suivi Matomo ({issue}`54`).
- Les liens modérateur et participant deviennent identifiables, avec `/admin/` et `/guest/` dans les URL ({issue}`93`).
- L'académie devient un paramètre de la création d'un salon ({issue}`80`).
- Parcours de suppression d'un salon ({issue}`90`).
- Information sur la limite de conservation des enregistrements ({issue}`98`).
- Tableau de bord et choix entre réunion immédiate et salon permanent ({issue}`75`).
- Pages d'erreur statiques ({issue}`81`).
- Documentation des options de configuration ({issue}`10`).

### Modifié

- La casse des noms provenant du SSO est forcée ({issue}`47`).

### Corrigé

- Ajout de `https://` à l'URL du Nuage récupérée depuis LaBoîte ({issue}`48`).
- Les tables sont bien créées lors d'une primo-installation ({issue}`78`).
- Page d'atterrissage erronée au lancement d'une visio depuis B3Desk ({issue}`77`).
- Soupçons de problème de charge ({issue}`76`).

<a id='changelog-1.1.6'></a>
## v1.1.6 — 2024-03-19

### Corrigé

- Rétroportage du correctif masquant l'affichage du PDF par défaut lorsque `FILE_SHARING` est activé ({pr}`117`).

<a id='changelog-1.1.5'></a>
## v1.1.5 — 2024-03-14

### Corrigé

- Plantage de `alembic_helper` lors de la recherche d'existence d'une table, notamment en cas de perte de numéro de migration.

<a id='changelog-1.1.4'></a>
## v1.1.4 — 2024-03-12

### Configuration

- Le paramètre `OIDC_INTROSPECTION_AUTH_METHOD` définit la manière dont B3Desk se connecte au point d'accès d'introspection du serveur d'identité.

### Corrigé

- Divers correctifs sur l'API des salons, à destination des greffons Thunderbird et Outlook.

<a id='changelog-1.1.3'></a>
## v1.1.3 — 2024-01-26

### Ajouté

- Page d'erreur statique pour nginx ({issue}`81`).

<a id='changelog-1.1.2'></a>
## v1.1.2 — 2023-12-08

### Corrigé

- Correction additionnelle du plantage de la zone de dépôt de fichiers ({issue}`58`, {pr}`64`).

<a id='changelog-1.1.1'></a>
## v1.1.1 — 2023-12-07

### Corrigé

- Chemin de téléversement des fichiers de conférence ({pr}`59`).
- Helper de migration Alembic pour le test d'existence des colonnes en base de données ({issue}`49`).

<a id='changelog-1.1.0'></a>
## v1.1.0 — 2023-10-25

### Configuration

- Les variables `OIDC_SCOPES` et `OIDC_ATTENDEE_SCOPES` sont lues depuis l'environnement ({pr}`7`).
- L'URL du sondage de satisfaction devient personnalisable ({issue}`12`, {pr}`29`).

### Ajouté

- Option permettant de désactiver l'authentification des participants ({issue}`9`, {pr}`11`).
- Message d'attente à l'entrée d'un séminaire ({issue}`13`, {pr}`34`).
- Gabarit personnalisé pour les erreurs 400 ({issue}`27`, {pr}`37`).
- Affichage du numéro de version en pied de page ({issue}`25`, {pr}`31`, {pr}`45`).

### Corrigé

- Variable `%%CONFNAME%%` dans la description d'un séminaire ({issue}`18`, {pr}`19`).
- Couleur de l'indicateur de chargement ({issue}`13`, {pr}`40`).

<a id='changelog-1.0.2'></a>
## v1.0.2 — 2023-07-18

### Ajouté

- Le projet est publié sous licence EUPL.

<a id='changelog-1.0.0'></a>
## v1.0.0 — 2023-07-17

Première publication du dépôt public de l'interface BigBlueButton fournie et utilisée par le ministère de l'Éducation nationale.

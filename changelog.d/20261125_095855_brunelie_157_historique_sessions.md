### Migrations

- [`8ad73a0e3e3b`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/8ad73a0e3e3b_create_meeting_session_table.py) crée la table `meeting_session`, qui garde une ligne par session BBB d'un salon : début, fin, nombre de participants et identifiant de l'enregistrement associé ({issue}`157` {user}`funelie`).
- [`ab83ad29acc9`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/ab83ad29acc9_session_history.py) crée la table `session_attendee`, qui garde pour chaque session le nom des participants, leur rôle de modérateur, leur première arrivée, leur dernier départ et leur temps de présence ({issue}`157` {user}`funelie`).

Ces deux migrations ne reprennent pas les données passées : seules les sessions lancées après la mise à jour figurent dans l'historique. Les enregistrements déjà présents sur BBB restent affichés, sans durée de session ni participants.

### Configuration

- `BIGBLUEBUTTON_ANALYTICS_CALLBACK_URL` change de rôle. BBB envoie désormais toujours ses données d'analytics à B3Desk, sur `/bbb-callback/analytics`, pour clore chaque session avec ses horaires réels et sa liste de participants. Quand le paramètre est renseigné, B3Desk transmet ensuite le contenu reçu à cette URL sans le modifier, avec le même en-tête `Authorization`, et fait jusqu'à trois tentatives. Le service d'analytics tiers continue donc de recevoir les mêmes données, mais c'est B3Desk qui les lui envoie et non plus BBB. Si le paramètre reste vide, comme par défaut, rien n'est transmis ({issue}`157` {user}`funelie`).

### Ajouté

- Une page d'historique par salon liste toutes ses sessions avec leur date, leur durée, leur nombre de participants et leur enregistrement s'il y en a un. Pour chaque session, on peut afficher la liste des participants, leurs horaires d'arrivée et de départ et leur rôle de modérateur. Un filtre permet de n'afficher que les sessions enregistrées ({issue}`157` {user}`funelie`).

### Modifié

- La page des enregistrements devient la page d'historique, et son adresse passe de `/meeting/recordings/<salon>` à `/meeting/history/<salon>`. Les anciens liens ne fonctionnent plus ({issue}`157` {user}`funelie`).
- Le bouton qui ouvre cette page est désormais toujours affiché, même quand l'enregistrement (`RECORDING`) est désactivé ({issue}`157` {user}`funelie`).
- La colonne de contenu principale est plus large sur les écrans moyens et grands.

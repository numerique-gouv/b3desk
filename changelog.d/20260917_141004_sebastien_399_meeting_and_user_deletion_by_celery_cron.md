### Migrations

Ce que la mise à jour change dans la base de données, avec l'identifiant de révision. Ces migrations sont appliquées automatiquement au démarrage : la rubrique sert à savoir quoi sauvegarder avant, et ce qui ne sera pas réversible.

- [`b7d4e2f81c30`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/b7d4e2f81c30_backfill_is_shadow_and_make_it_not_null.py) rend `is_shadow` non nul dans la table `meeting`.
- [`c1f9c8e6a3d2`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/c1f9c8e6a3d2_add_information_level_to_meeting_and_.py) ajoute `information_level` dans les tables `user` et `meeting`.

### Configuration

- INACTIVITY_TIMER_CLEANUP_MEETING : durée d'existence d'un meeting inactif
- INACTIVITY_TIMER_CLEANUP_ACCOUNT : durée d'existence d'un compte utilisateur inactif
- DAILY_MEETING_CLEANUP_TIME : heure de suppression des meetings inactifs
- DAILY_ACCOUNT_CLEANUP_TIME : heure de suppression des comptes inactifs
- DAILY_EMAIL_BEFORE_MEETING_DELETION_TIME : heure d'envoi des mails avant suppression des meetings inactifs
- DAILY_EMAIL_BEFORE_ACCOUNT_DELETION_TIME : heure d'envoi des mails avant suppression des comptes inactifs
- CRON_DEFAULT_TIMEZONE : fuseau horaire utilisé pour le lancement des tâches quotidiennes

### Ajouté

- Fin de vie des objets utilisateurs et réunions ({pr}`406`, {user}`SbirLobo`).

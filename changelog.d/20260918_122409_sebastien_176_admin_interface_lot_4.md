### Migrations
[`15f860af6e2b`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/15f860af6e2b_add_academic_domains_excludelist_and_.py)
- Nouvelle table `excludelist`, dépend de `user_id` et `group_id`, avec un contrainte unique sur ce couple de clés. Cette table liste les utilisateurs exclus de groupes ({pr}`436`, {user}`SbirLobo`).
- Nouvelles colonnes dans `group` ({pr}`436`, {user}`SbirLobo`) :
    - `academic_codes` : liste de codes des académies (codaca issus du LDAP des utilisateurs de l'éducatin nationale)
    - `mail_domains`: liste de noms de domaines
- Nouvelle colonne dans `user` : `meta_data` au format JSON pour stocker certaines informations récupérées depuis le token d'identification des utilisateurs.

### Ajouté
- L'administrateur peut affiner la gestion des groupes ({pr}`436`, {user}`SbirLobo`) :
    - Inclure des académies dont les utilisateurs seront automatiquement affiliées au groupe lors de leur prochaine connexion au service
    - Inclure des affiliations automatiques par nom de domaine
    - Exclure des utilisateurs de groupes (le tri est fait en même temps que l'affiliation automamtique lors de la connexion de l'utilisateur)

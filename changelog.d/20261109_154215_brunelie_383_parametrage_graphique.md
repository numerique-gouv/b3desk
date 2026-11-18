### Migrations

- [`d8fdc258f263`](https://github.com/numerique-gouv/b3desk/blob/main/web/migrations/versions/d8fdc258f263_parametrage_affichage_bbb.py) ajoute quatre colonnes (booléens) à la table meeting : `showPresentationOnJoin`, `showParticipantsOnLogin` et `showPublicChatOnLogin`, qui sont True par défaut, et `showSessionDetailsOnJoin`, qui est False par défaut. Les meeting existants reçoivent ces valeurs par défaut. ({issue}`383`, {user}`funelie`, {pr}`404`).

### Ajouté

- Les organisateurs peuvent paramétrer les options d'affichage par défaut d'un meeting pour les participants, dans le formulaire de création d'un salon. Sont paramétrables : l'affichage par défaut de la présentation, de la liste des participants, le chat public, et la fenêtre d'informations de la session. ({issue}`383`, {user}`funelie`, {pr}`404`).

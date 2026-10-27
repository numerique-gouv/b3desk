### Sécurité
- Les mots de passe des salons, les codes PIN, les clés des liens d'invitation et les identifiants des salles BigBlueButton sont générés avec le module `secrets` au lieu de `random` et `uuid`, pour être imprévisibles ({pr}`459`, {issue}`419` et {user}`SbirLobo`).

# Publication

La branche de référence pour les releases est `production`. C'est ici qu'on retrouve les différentes versions installées sur les instances. À ces releases correspondent des tags git.

Pour publier une nouvelle version :
- S'assurer d'être sur la branche `production`
- Faire un merge de `main` dans `production` pour récupérer les dernières modifications. `main` devrait être dans une version de dev et supérieure à `production`. Ce merge devrait créer un conflit.
- Résoudre ce conflit en mettant à jour le numéro de version dans `pyproject.toml` et dans `web/b3desk/__init__.py` simplement en enlevant `dev` de la version.
- Nommer ce commit de merge "Merge branch 'main' X.Y.Zdev into production"
- Mettre un tag sur ce commit, portant le numéro de la version, avec `git tag -a vX.Y.Z -m "Bump to X.Y.Z version`
- Pousser le commit ET le tag `git push origin production --follow-tags` (ou `upstream` si `production` est référencé sur `upstream`)
- Se rendre sur [la page github de publication de version](https://github.com/numerique-gouv/b3desk/releases/new)
- Choisir le tag récemment ajouté, remplir les informations, publier la version.
- Repasser sur `main` pour passer cette branche sur la prochaine version dev `X.Y.Zdev`

Attention, pour que le numéro de version s'affiche correctement sur la version déployée,
il est nécessaire que le projet soit déployé avec git (c.à.d. qu'il y ait un dépôt git
qui soit déployé), et aussi que le commit qui soit déployé soit directement marqué par
un tag git. Dans les autres cas, c'est le numéro de commit qui sera affiché.

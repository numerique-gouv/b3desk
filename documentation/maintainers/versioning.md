# Publication de nouvelles versions

- Mettre un tag sur le commit, portant le numéro de la version, avec `git tag vX.Y.Z`
- Pousser le commit ET le tag `git push origin main --tags`
- Se rendre sur [la page github de publication de version](https://github.com/numerique-gouv/b3desk/releases/new)
- Choisir le tag récemment ajouté, remplir les informations, publier la version.

Attention, pour que le numéro de version s'affiche correctement sur la version déployée,
il est nécessaire que le projet soit déployé avec git (c.à.d. qu'il y ait un dépôt git
qui soit déployé), et aussi que le commit qui soit déployé soit directement marqué par
un tag git. Dans les autres cas, c'est le numéro de commit qui sera affiché.

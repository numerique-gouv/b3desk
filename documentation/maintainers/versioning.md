# Publication

Pour publier une nouvelle version :

## S'assurer que `main` est à jour

## Être sur la branche `production`

La branche de référence pour les releases est `production`. C'est ici qu'on retrouve les différentes versions installées sur les instances. À ces releases correspondent des tags git.

```
git branch
# La liste des branches sera affichée avec une * avant la branche actuelle.
```
Si la branche actuelle n'est pas `production` :
```
git switch production
```

## Récupérer les dernières modifications

Faire un merge de `main` dans `production` pour récupérer les dernières modifications prêtes à être publiées.
```
git merge main
```
`main` devrait être dans une version de dev et supérieure à `production`. Ce merge devrait créer deux conflits sur `pyproject.toml` et `web/b3desk/__init__.py`.

## Résoudre ces conflits

Résoudre les conflit en mettant à jour le numéro de version dans `pyproject.toml` et dans `web/b3desk/__init__.py` simplement en enlevant `dev` de la version.

## Lancer les tests avec `tox`
```bash
tox -p
```
Résoudre les erreurs éventuelles avant de recommencer la procédure.

## Nommer ce commit

Pour simplifier l'historique du versionnement on nomme ce merge "Merge branch 'main' W.X.Ydev into production"

```
git add <fichiers modifiés>
# exemple : git add pyproject.toml web/b3desk/__init__.py
git commit -m "Merge branch 'main' W.X.Ydev into production"
# exemple : git commit -m "Merge branch 'main' 1.2.20dev into production"
```

## Ajouter un tag

Mettre un tag sur ce commit, portant le numéro de la version

```
git tag -a vW.X.Y -m "Bump to W.X.Y version"
# exemple : git tag -a v1.2.20 -m "Bump to 1.2.20 version"
```

Le pousser avec le commit, sur upstream si l'on travaille depuis un fork.

```
git push upstream production --follow-tags
```

## Publier la nouvelle version

Se rendre sur [la page github de publication de version](https://github.com/numerique-gouv/b3desk/releases/new).

Choisir le tag récemment ajouté, préciser les ticket fermés par la release, indiquer s'il y a de nouvelles migrations, de la configuration à ajouter, publier la version.

## Mettre `main` à jour

Repasser sur `main`

```
git switch main
```

Passer cette branche sur la prochaine version dev `W.X.Zdev` dans les fichiers `pyproject.toml` et `web/b3desk/__init__.py`.

Nommer ce commit "Update main to W.X.Zdev version".

```
git add pyproject.toml web/b3desk/__init__.py
git commit -m "Update main to W.X.Zdev version"
# exemple : git commit -m "Update main to 1.2.21dev version"
```

Pousser ce commit sur upstream

```
git push upstream main
```

⚠️ Attention, pour que le numéro de version s'affiche correctement sur la version déployée, il est nécessaire que le projet soit déployé avec git (c.à.d. qu'il y ait un dépôt git qui soit déployé), et aussi que le commit qui soit déployé soit directement marqué par un tag git. Dans les autres cas, c'est le numéro de commit qui sera affiché.

# Publication

Pour publier une nouvelle version :

## S'assurer que `main` est à jour

Le journal des modifications et le numéro de version sont préparés sur `main`,
puis reportés sur `production` par le merge habituel. Commencez donc par vous
placer sur `main` et par récupérer les dernières modifications.

```
git switch main
git pull upstream main
```

## Fixer le numéro de version

Enlever `dev` du numéro de version dans les fichiers `pyproject.toml` et
`web/b3desk/__init__.py`. La version passe par exemple de `1.2.20dev` à
`1.2.20`.

## Rassembler le journal des modifications

```
just changelog-collect
```

[scriv](https://scriv.readthedocs.io) déplace les fragments du dossier
`changelog.d` dans le fichier `CHANGELOG.md`, sous un titre reprenant le
numéro de version qu'il lit dans `pyproject.toml` — d'où l'ordre de ces deux
étapes. Le fichier s'ouvre ensuite dans votre éditeur : c'est le moment de
relire l'entrée, de fusionner les formulations redondantes et de vérifier que
les rubriques « Actions requises » et « Configuration » disent bien tout ce
qu'une personne qui administre une instance doit savoir avant de mettre à
jour. Ce texte sera publié tel quel dans les notes de la release.

## Lancer les tests avec `tox`
```bash
tox -p
```
Résoudre les erreurs éventuelles avant de recommencer la procédure.

## Nommer ce commit

```
git add pyproject.toml web/b3desk/__init__.py CHANGELOG.md changelog.d
git commit -m "chore: prepare the W.X.Y release"
# exemple : git commit -m "chore: prepare the 1.2.20 release"
git push upstream main
```

## Être sur la branche `production`

La branche de référence pour les releases est `production`. C'est ici qu'on retrouve les différentes versions installées sur les instances. À ces releases correspondent des tags git.

```
git switch production
```

## Récupérer les dernières modifications

Faire un merge de `main` dans `production` pour récupérer les dernières modifications prêtes à être publiées, numéro de version et journal des modifications compris.

```
git merge main
```

En cas de conflit sur `pyproject.toml`, `web/b3desk/__init__.py` ou
`CHANGELOG.md`, conserver systématiquement la version de `main`, qui est celle
que l'on publie.

Pour simplifier l'historique du versionnement on nomme ce merge "Merge branch 'main' W.X.Y into production".

```
git commit -m "Merge branch 'main' W.X.Y into production"
# exemple : git commit -m "Merge branch 'main' 1.2.20 into production"
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

La release est publiée automatiquement par GitHub Actions à la réception du
tag. Le workflow construit les paquets, les attache à la release, puis écrit
les notes de version à partir de l'entrée correspondante du `CHANGELOG.md`. Il
n'y a donc rien à compléter à la main sur [la page des
releases](https://github.com/numerique-gouv/b3desk/releases) : si le texte
publié ne convient pas, corrigez l'entrée dans `CHANGELOG.md` et relancez le
workflow, plutôt que d'éditer la release depuis l'interface de GitHub — une
modification faite là serait écrasée à la prochaine exécution, et surtout elle
ne se retrouverait pas dans le dépôt.

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

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

Enlever le suffixe de développement du numéro de version dans le champ
`version` de `pyproject.toml`. La version passe par exemple de `1.2.20.dev0` à
`1.2.20`. Les numéros suivent [PEP 440](https://peps.python.org/pep-0440/).

## Rassembler le journal des modifications

```
just changelog-collect
```

[scriv](https://scriv.readthedocs.io) déplace les fragments du dossier
`changelog.d` dans le fichier `CHANGELOG.md`, sous un titre reprenant le
numéro de version qu'il lit dans `pyproject.toml` — d'où l'ordre de ces deux
étapes. Le fichier s'ouvre ensuite dans votre éditeur : c'est le moment de
relire l'entrée, de fusionner les formulations redondantes et de vérifier que
les rubriques « Actions requises », « Migrations » et « Configuration » disent
bien tout ce qu'une personne qui administre une instance doit savoir avant de
mettre à jour. Ce texte sera publié tel quel dans les notes de la release.

## Lancer les tests avec `tox`
```bash
tox -p
```
Résoudre les erreurs éventuelles avant de recommencer la procédure.

## Nommer ce commit

```
git add pyproject.toml CHANGELOG.md changelog.d
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

En cas de conflit sur `pyproject.toml` ou `CHANGELOG.md`, conserver systématiquement la version de `main`, qui est celle
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

Passer cette branche sur la prochaine version de développement `W.X.Z.dev0` dans `pyproject.toml`.

Nommer ce commit "Update main to W.X.Z.dev0 version".

```
git add pyproject.toml
git commit -m "Update main to W.X.Z.dev0 version"
# exemple : git commit -m "Update main to 1.2.21.dev0 version"
```

Pousser ce commit sur upstream

```
git push upstream main
```

⚠️ Le numéro affiché en pied de page est celui que portait `pyproject.toml` au moment de la construction de l'image Docker, lu dans les métadonnées du paquet installé. Une instance qui n'a pas reconstruit son image continue donc d'afficher la version précédente, même si son dépôt est à jour.

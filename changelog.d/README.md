# Fragments du journal des modifications

Ce dossier accueille les fragments que [scriv](https://scriv.readthedocs.io)
rassemblera dans le [`CHANGELOG.md`](../CHANGELOG.md) au moment de la
publication d'une version. Chaque pull request qui change quelque chose pour
les personnes qui utilisent ou administrent B3Desk y dépose un fichier :

```bash
uv run scriv create --edit
```

Écrire le fragment au moment de la pull request plutôt qu'au moment de la
publication évite deux écueils : les conflits systématiques sur un fichier
unique, et l'oubli du détail qui compte pour l'administrateur — la migration à
lancer, le paramètre à ajouter — que personne ne retrouve trois semaines plus
tard en relisant les titres de commits.

Le format d'un fragment et le sens de chaque rubrique sont décrits dans le
modèle [`new_fragment.md.j2`](new_fragment.md.j2), recopié en commentaire dans
chaque nouveau fichier. Les fragments disparaissent lorsqu'ils sont collectés ;
leur contenu vit alors dans `CHANGELOG.md`.

Les tickets et les personnes se référencent avec les rôles de sphinx-issues,
`` {pr}`366` ``, `` {issue}`226` `` et `` {user}`azmeuk` ``. Le workflow de
publication les remplace par des liens avant de remplir les notes de release ;
tout nouveau rôle employé ici demande donc une règle supplémentaire dans
`.github/workflows/Release.yml`.

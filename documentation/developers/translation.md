# Traductions

## Ajouter du texte à traduire

Lorsque vous ajoutez du texte qui doit être traduit dans les templates html, vous devez les mettre dans un bloc :
```html
{% trans %}Texte à traduire{% endtrans %}
```
Dans le code python, vous devez utiliser :
```python
lazy_gettext("Texte à traduire")
```

Vous devez ensuite extraire ces messages à traduire pour qu'ils soient ajoutés au fichier `web/translations/messages.pot` avec :
```shell
just translation-extract
```

Vous pouvez ensuite mettre à jour les "catalogues" des différentes langues avec :
```shell
just translation-update
```
Cette commande va mettre à jour les "catalogues" existants avec de nouveaux messages (sans écraser ceux qui ont déjà été traduits).

## Traduire du texte

Les traductions sont gérées via [Weblate](https://hosted.weblate.org/projects/B3desk/). Weblate synchronise automatiquement les traductions avec le dépôt Git (branche `main`).

Lors de la traduction, il ne faut pas traduire les motifs du type `%(...)s` mais simplement mettre l'équivalent traduit.
Par exemple, pour une traduction vers l'anglais :

```po
msgid "Inviter quelqu'un à %(this_meeting)s."
msgstr "Invite someone to this meeting."
```

### Développement local

Pour tester les traductions en local, vous devez compiler les "catalogues" :
```shell
just translation-compile
```
Il faut ensuite reconstruire le conteneur web, par exemple avec :
```shell
docker compose up web -d --build
```

## Ajouter une langue

Vous pouvez ajouter une nouvelle langue avec :
```shell
pybabel init --input-file web/translations/messages.pot --output-dir web/translations --locale LANG
```
Vous devez ensuite suivre les étapes précédentes pour faire la traduction dans cette nouvelle langue.

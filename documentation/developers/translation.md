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
Cette commande va mettre à jour les catalogues existants avec de nouveaux messages (sans écraser ceux qui ont déjà été traduits) que vous pouvez alors traduire dans la langue voulue.

## Traduire du texte

Les fichiers à traduire sont `web/b3desk/translations/*/LC_MESSAGES/messages.po`.
Lors de la traduction, il ne faut pas traduire les motifs du type `%(...)s` mais simplement mettre l'équivalent traduit.
Par exemple, pour une traduction vers l'anglais :

```po
msgid "Inviter quelqu'un à %(this_meeting)s."
msgstr "Invite someone to this meeting."
```

Une fois les traductions réalisées, vous devez compiler le catalogue pour qu'elle soient visible pour l'utilisateur avec :
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

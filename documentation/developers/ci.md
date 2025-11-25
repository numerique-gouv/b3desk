# Intégration Continue

Quand l’intégration continue (CI) s’est correctement déroulée, l’interface de github affiche cet encart :

![ci](../_static/ci.png)

Les différentes étapes de l’intégration continue

## Tests dans un virtualenv

GitHub Actions fait passer la suite de test sur un virtualenv.

Pour passer cette étape, il faut que `pytest` soit vert sur votre environnement local.

## Tests dans un conteneur

GitHub Actions fait passer la suite de test dans un conteneur Docker.

Pour passer cette étape, il faut que la commande `docker-compose run --rm tests` soit verte sur votre machine.

## Healthcheck sur les conteneurs

GitHub Actions lance tous les conteneurs requis pour un environnement de développement local et fait un healthcheck sur chacun. Certains vont vérifier que le service fonctionne, d'autres on besoin de valider que les ocnteneurs peuvent communiquer entre eux.

Cela permet d'assurer que le code reste fonctionnel lorsqu'on lance le projet de zéro sur une nouvelle machine, et qu'il est donc possible d'embarquer de nouvelles·aux contributeur·rice·s.

## Couverture de code croissante

GitHub Actions va vérifier que la couverture de test de la pull request est correcte.

Toutes les lignes de code modifiées lors de la PR doivent être couvertes.

Cela permet d'augmenter au fur et à mesure ce que les tests vont couvrir et donc d'assurer de plus en plus l'état fonctionnel du projet.

Pour être sûr de passer cette étape, il suffit d'ajouter des tests **au moins** sur le code que vous modifiez.

## Formattage du code

GitHub Actions va vérifier que le code a bien été formatté :

- Les espaces de fin de ligne sont supprimés.
- Les imports python sont triés
- Le code est formatté à l’aide de `ruff`
- Quelques vérifications statiques sont effectuées avec `ruff`

À l’avenir, `mypy` pourrait être utilisé.

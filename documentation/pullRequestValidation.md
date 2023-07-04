# Validation de Pull Request

Pour qu'une pull request soit validée par les mainteneurs, elle doit passer un certain nombre d'étapes :

## CI : Tests dans un virtualenv

GitHub Actions fait passer la suite de test sur un virtualenv.

Pour passer cette étape, il faut que `pytest` soit vert sur votre environnement local.

## CI : Tests dans un conteneur

GitHub Actions fait passer la suite de test dans un conteneur Docker.

Pour passer cette étape, il faut que la commande `docker-compose run --rm tests` soit verte sur votre machine.

## CI : Healthcheck sur les conteneurs

GitHub Actions lance tous les conteneurs requis pour un environnement de développement local et fait un healthcheck sur chacun. Certains vont vérifier que le service fonctionne, d'autres on besoin de valider que les ocnteneurs peuvent communiquer entre eux.

Cela permet d'assurer que le code reste fonctionnel lorsqu'on lance le projet de zéro sur une nouvelle machine, et qu'il est donc possible d'embarquer de nouvelles·aux contributeur·rice·s.

## CI : Couverture de code croissante

GitHub Actions va vérifier que la couverture de test de la pull request est au moins égale à celle du dernier commit.

Cela permet d'augmenter au fur et à mesure ce que les tests vont couvrir et donc d'assurer de plus en plus l'état fonctionnel du projet.

Pour être sûr de passer cette étape, il suffit d'ajouter des tests **au moins** sur le code que vous modifiez.

## CI : Formattage du code

GitHub Actions va vérifier que le code a bien été formatté. Pour le moment, seul `black` est exécuté, mais à l'avenir, `flake8` ou encore `mypy` pourraient être requis. Le même genre de décisions pourait être appliquée au front.

## Tests en préprod

Passé ces étapes, les mainteneurs font une validation manuelle des développements réalisés.

Sur un serveur de préprod, il faut récupérer la *pull request* en question :
```bash
git fetch origin pull/ID/head:BRANCH_NAME
```
en remplaçant `ID` par l'**id** de la pull request et `BRANCH_NAME` par le nom de la **branche** sur laquelle ont été réalisés les modifications, celle du *fork*.

Il faut ensuite passer sur cette branche puis lancer la préprod :
```bash
git switch BRANCH_NAME
# Switched to a new branch 'BRANCH_NAME'
docker compose -f docker-compose.yml -f docker-compose.preprod.yml up
```

À partir de là, l'état fonctionnel du projet peut être testé manuellement ainsi que les modifications apportées par la PR.

Lorsqu'assez de modifications suffisamment cohérentes ont été ajoutées sur la branche `main`, les mainteneurs peuvent merger celle-ci dans la branche `production` qui sert de référence pour les déploiements. Un tag avec un numéro de version ainsi qu'un changelog peut également être ajouté.

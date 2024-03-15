# Revue de code

Les correctifs et évolutions nécessitant une validation de l’équipe produit font l’objet de *pull request (PR)* sur le dépôt GitHub.

Le *périmètre technique* est la responsabilité de l’équipe de développement.
Elle est donc autonome pour valider les modifications de code touchant à la qualité, aux réusinages etc.

Le *périmètre fonctionnel* est la responsabilité de l’équipe produit.
C’est donc à elle de valider les modifications touchant aux fonctionnalités, et certaines corrections, en suivant le processus suivant.

## 1. S’assurer que la CI est bien verte

Quand l’intégration continue (CI) s’est correctement déroulée, l’interface de github affiche cet encart :

![ci](../_static/ci.png)

Ne pas valider un PR qui ne passerait pas la batterie de tests automatiques de la CI.
Plus de détails sur l’intégration continue sont disponibles dans la {ref}`section dédiée <developers/ci:Intégration Continue>`.

## 2. Déployer la PR dans un environnement de test

Passées ces étapes, les mainteneurs font une validation manuelle des développements réalisés.

Sur un serveur de préprod, il faut récupérer la PR en suivant les instructions de la {ref}`section déploiement <maintainers/deployment:Téléchargement du code source>`

## 3. Tests fonctionnels

Sur l’instance de test, vérifier que les corrections ou fonctionnalités correspondent aux attentes, et ne créent pas d’effets de bord indésirables.

S’il y a des choses à améliorer, commenter dans le fil de discussion de la PR sur github, puis reprendre à l’étape 1 lorsque des corrections sont appportées.
Il suffira d’effectuer un `git pull origin pr<ID>` pour mettre le code à jour.

## 4. Fusionner.

Enfin, lorsque tout semble bon, fusionner la Pull Request sur Github.

Configuration
#############

B3Desk
======

L’ensemble des paramètres décrits sur cette page peuvent être passées en variables d’environnement à l’application B3Desk.

.. autopydantic_model:: b3desk.settings.MainSettings

Nginx
=====

B3Desk fournit des pages d'erreurs statiques qui peuvent être affichées en cas de problème.
Pour utiliser ces pages statiques, on peut utiliser le paramètre `error_page <https://nginx.org/en/docs/http/ngx_http_core_module.html#error_page>`_ de Nginx::

    error_page 500 502 503 504 /static/errors/custom_50x.html;

Avec cette configuration, dès que le service est indisponible, Nginx servira cette page d'erreur:

.. image:: ../_static/b3desk-500.png


Jumelage avec Apps
==================

Configuration de B3Desk
-----------------------

Afin que les utilisateurs de b3desk puissent accéder à leurs fichiers Nextcloud d’Apps, il faut que l’application puisse récupérer l’identifiant attendu par Nextcloud. Pour ce faire une requête est faite sur l’`API Users de Keycloak <https://www.keycloak.org/docs-api/22.0.1/rest-api/index.html#_users>`_.

Il est donc nécessaire de configurer les paramètres de configuration suivants :

- :attr:`~b3desk.settings.MainSettings.SECRET_KEY` (TODO)
- :attr:`~b3desk.settings.MainSettings.SECRET_KEY` (TODO)
- :attr:`~b3desk.settings.MainSettings.SECRET_KEY` (TODO)

On peut ensuite tester que la configuration est correcte grâce à la commande suivante:

.. code-block:: bash

   docker exec -it <CONTAINER_ID> flask get-apps-id <email@example.com>

En remplaçant ``<CONTAINER_ID>`` par l’identifiant du conteneur `b3desk_web`, et ``<email@example.com>`` par l’email d’un utilisateur, cette commande tente une connexion à l’API keycloak d’apps, afin de récupérer l’identifiant dont l’email a été passé en paramètre.

Si la connexion à l’API de keycloak échoue, cette commande indiquera à quelle étape, et quelles sont les pistes de résolution.

Configuration de Keycloak
-------------------------

Pour que la connexion de B3Desk à Apps fonctionne correctement, il est nécessaire que keycloak autorise les connexion par `identifiants client <https://datatracker.ietf.org/doc/html/rfc6749#section-4.4>`_.

Vérifier que la configuration de Keycloak est correcte
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Se rendre la console d’administration Keycloak, dans le `realm` ``apps``.
  Par exemple https://auth.eole3.dev/auth/admin/master/console/#/apps
- Se rendre dans la section « Clients » et sélectionner « b3desk »
- Sélectionner l’onglet « Service account roles »
- À cet endroit on doit voir deux lignes avec les droits ``real-management view-users`` et ``realm-management query-users``.

.. image:: ../_static/keycloak-service-account-roles.png

Configuration de Keycloak est correcte
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Si les droits ``real-management view-users`` et ``realm-management query-users`` ne sont pas présents, il faut les ajouter :

- Cliquer sur le bouton « Assign roles », une fenêtre modale doit s’ouvrir
- Cliquer sur le menu déroulant des filtres en haut à gauche, et sélectionner « Filter by clients » plutôt que « Filter by realm roles »
- Dans le champ de recherche, entrer « users » et valider
- Cocher « view-users » et « query-users » puis sur le bouton « Assign »

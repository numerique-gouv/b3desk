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

Il est donc nécessaire de configurer les paramètres de configuration suivants :

- :attr:`~b3desk.settings.MainSettings.SECONDARY_IDENTITY_PROVIDER_ENABLED`
- :attr:`~b3desk.settings.MainSettings.SECONDARY_IDENTITY_PROVIDER_URI`
- :attr:`~b3desk.settings.MainSettings.SECONDARY_IDENTITY_PROVIDER_REALM`
- :attr:`~b3desk.settings.MainSettings.SECONDARY_IDENTITY_PROVIDER_CLIENT_ID`
- :attr:`~b3desk.settings.MainSettings.SECONDARY_IDENTITY_PROVIDER_CLIENT_SECRET`

On peut ensuite tester que la configuration est correcte grâce à la commande suivante :

.. code-block:: bash

   docker exec -it <CONTAINER_ID/NAME> flask get-apps-id <email@example.com>

En remplaçant ``<CONTAINER_ID/NAME>`` par l’identifiant du conteneur `b3desk_web` ou simplement son nom, et ``<email@example.com>`` par l’email d’un utilisateur, cette commande tente une connexion à l’API keycloak d’apps, afin de récupérer l’identifiant dont l’email a été passé en paramètre.

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


Utilisation d'un materiel visio SIPMediaGW
==========================================

Configuration de la SIP dans B3Desk
-----------------------------------

Afin de permettre au matériel visio SIPMediaGW de rejoindre une visio via B3Desk, il faut lui communiquer un token qui sécurisera la connexion à B3Desk.

Dans un premier temps, il faut générer une clé privée :

.. code-block:: bash

   docker exec -it <CONTAINER_ID/NAME> flask generate-private-key

En remplaçant ``<CONTAINER_ID/NAME>`` par l’identifiant du conteneur b3desk_web ou simplement son nom, cette commande va générer une clé privée qui sera affectée à l'instance B3Desk.
Afin de permettre que les tokens générés avec cette clé privée soient reconnus par tous les serveurs, il convient d'utiliser la même clé privée sur tous les serveurs d'une même instance B3Desk.

On peut ensuite configurer les paramètres suivants de manière identique pour tous les serveurs d'une même instance B3Desk :

- :attr:`~b3desk.settings.MainSettings.ENABLE_SIP`
- :attr:`~b3desk.settings.MainSettings.FQDN_SIP_SERVER`
- :attr:`~b3desk.settings.MainSettings.PRIVATE_KEY`

.. code-block:: bash
   :caption: web.env

   ENABLE_SIP=on
   FQDN_SIP_SERVER=example.serveur.com
   PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
   ThereIsAWonderfulPrivateKey
   -----END PRIVATE KEY-----"

.. warning::
   Pour les données s'étalant sur plusieurs lignes, pensez à les entourer de guillements doubles ``"``.

Il est maintenant nécessaire de redémarrer le conteneur de chaque serveur :

.. code-block:: bash

   docker compose -f docker-compose.yml -f docker-compose.prod.yml web -d

Il est possible de vérfier que le paramétrage a été correctement effectué :

.. code-block:: bash

   docker exec -it <CONTAINER_ID/NAME> flask check-sip-setttings

Générer un sip-token
--------------------

Une fois que B3Desk est correctement paramétré, la généreration de sip-token est active :

.. code-block:: bash

   docker exec -it <CONTAINER_ID/NAME> flask generate-sip-token

Ce token est valide sans limite de temps, tant que la clé privée reste la même. Un même token pourra servir pour plusieurs services différents de visio SIPMediaGW tant qu'ils requêtent la même instance possèdant la bonne clé privée.

Vous pouvez vérifier que le token est valide avec la commande :

.. code-block:: bash

   docker exec -it <CONTAINER_ID/NAME> flask check-sip-token "<token>"

Il suffira de transmettre ce token au matériel SIP qui devra le joindre dans le header ``{"Authorization": <token>}`` lors de ses requêtes sur la route suivante : ``https://<instance_b3desk>/sip-connect/<visio_code>``


Gestion des administrateurs
===========================

Les administrateurs ne sont pas des utilisateurs de B3Desk : ils ne sont pas enregistrés en base de données.
Ils se connectent au backoffice via un serveur d’identité OpenID Connect dédié, par exemple `Canaille <https://canaille.readthedocs.io>`_, distinct de celui des utilisateurs.

Le backoffice est désactivé par défaut.
Tant qu’il est désactivé, la page ``/admin/login`` renvoie une erreur 404 et aucun administrateur ne peut se connecter.

Configurer le serveur d’identité des admins
-------------------------------------------

Dans Canaille :

1. créez un client OpenID Connect pour B3Desk avec :

   - l’URL de redirection ``https://<instance_b3desk>/oidc_callback`` ;
   - l’URL de redirection après déconnexion ``https://<instance_b3desk>/logout`` ;
   - les scopes ``openid``, ``profile``, ``email`` et ``groups`` ;

2. créez un groupe d’administration, nommé ``admin`` par défaut ;
3. créez un compte pour chaque administrateur et ajoutez-le à ce groupe.

Créez les comptes administrateurs sans mot de passe, pour ne pas en laisser dans l’historique du shell.
Aucun mail n’est envoyé à la création : à sa première connexion, l’administrateur saisit son identifiant et Canaille lui propose de recevoir par mail un lien pour définir son mot de passe.
Canaille doit pour cela être configuré avec un serveur SMTP ; sans SMTP, un compte sans mot de passe ne peut pas se connecter.
Le SMTP se configure dans la section ``[CANAILLE.SMTP]`` du fichier de configuration de Canaille, ou par variables d’environnement :

.. code-block:: bash

   CANAILLE__SMTP__HOST=smtp.example.com
   CANAILLE__SMTP__PORT=587
   CANAILLE__SMTP__TLS=true
   CANAILLE__SMTP__LOGIN=<login>
   CANAILLE__SMTP__PASSWORD=<mot_de_passe>
   CANAILLE__SMTP__FROM_ADDR=admin@example.com

Consultez la `documentation de Canaille <https://canaille.readthedocs.io>`_ pour la création des clients, groupes et comptes.
La :doc:`documentation de contribution <../developers/contributing>`, section « Se connecter en administrateur avec Canaille », donne un exemple complet de ces commandes sur l’instance Canaille locale de développement.

Configurer B3Desk
-----------------

.. code-block:: bash

   OIDC_ADMIN_ENABLED=on
   OIDC_ADMIN_ISSUER=https://<instance_canaille>
   OIDC_ADMIN_CLIENT_ID=<client_id>
   OIDC_ADMIN_CLIENT_SECRET=<client_secret>
   OIDC_ADMIN_SCOPES=openid, profile, email, groups
   OIDC_ADMIN_GROUP=admin
   OIDC_ADMIN_SESSION_LIFETIME=3600

B3Desk refuse de démarrer si ``OIDC_ADMIN_ENABLED`` est activé sans ``OIDC_ADMIN_ISSUER``.
Le détail de chaque paramètre est décrit dans la section `B3Desk`_.

Connexion des administrateurs
-----------------------------

Les administrateurs se connectent sur ``https://<instance_b3desk>/admin/login``.
Seuls les comptes membres du groupe ``OIDC_ADMIN_GROUP`` obtiennent l’accès au backoffice.

- une session administrateur et une session utilisateur ne peuvent pas coexister : se connecter avec l’une ferme l’autre ;
- la session administrateur expire après ``OIDC_ADMIN_SESSION_LIFETIME`` secondes, sans être prolongée par l’activité ;
- la déconnexion ferme aussi la session sur le serveur d’identité des admins.

Donner ou retirer les droits admin
----------------------------------

Les droits admin se gèrent uniquement dans le serveur d’identité : ajoutez ou retirez le compte du groupe ``OIDC_ADMIN_GROUP``.
Un retrait prend effet à la prochaine connexion de l’administrateur, ou au plus tard à l’expiration de sa session.

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

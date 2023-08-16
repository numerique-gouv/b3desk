# -*- coding: utf-8 -*-
# +----------------------------------------------------------------------------+
# | BBB-VISIO                                                                  |
# +----------------------------------------------------------------------------+
#
#   This program is free software: you can redistribute it and/or modify it
# under the terms of the European Union Public License 1.2 version.
#
#   This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.

from flask import Flask, request, session
import os
import logging

from flask_babel import Babel
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from .common.extensions import cache

CRITICAL_VARS = ["OIDC_ISSUER", "OIDC_CLIENT_SECRET", "BIGBLUEBUTTON_SECRET"]
LANGUAGES = ["en", "fr"]


def setup_babel(app):
    babel = Babel(app)

    @babel.localeselector
    def get_locale():
        if request.args.get("lang"):
            session["lang"] = request.args["lang"]
        return session.get("lang", "fr")


def create_app(test_config=None, gunicorn_logging=False):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    cache.init_app(
        app,
        config={
            "CACHE_TYPE": "flask_caching.backends.filesystem",
            "CACHE_DIR": "/tmp/flask-caching",
        },
    )
    if gunicorn_logging:
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)
    app.config.from_pyfile("config.py")
    if test_config:
        app.config.from_mapping(test_config)

    @app.context_processor
    def global_processor():
        return {
            "config": app.config,
            "beta": app.config["BETA"],
            "documentation_link": app.config["DOCUMENTATION_LINK"],
            "LANGUAGES": LANGUAGES,
            **app.config["WORDINGS"],
        }

    # translations
    setup_babel(app)

    # Protect App Form with CSRF
    csrf = CSRFProtect()
    csrf.init_app(app)

    # init database
    with app.app_context():
        import flaskr.routes

        app.register_blueprint(flaskr.routes.bp)
        from .models import db

        db.init_app(app)
        Migrate(app, db, compare_type=True)

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    return app

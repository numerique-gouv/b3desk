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
import logging
import os

from b3desk.settings import MainSettings
from b3desk.utils import is_rie
from flask import Flask
from flask import render_template
from flask import request
from flask_babel import Babel
from flask_caching import Cache
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFError
from flask_wtf.csrf import CSRFProtect


CRITICAL_VARS = ["OIDC_ISSUER", "OIDC_CLIENT_SECRET", "BIGBLUEBUTTON_SECRET"]
LANGUAGES = ["en", "fr"]

babel = Babel()
cache = Cache()
csrf = CSRFProtect()


def setup_configuration(app, config=None):
    if config:
        app.config.from_mapping(config)

    config_obj = MainSettings.model_validate(config or {})
    app.config.from_object(config_obj)


def setup_cache(app):
    cache.init_app(
        app,
        config={
            "CACHE_TYPE": "flask_caching.backends.filesystem",
            "CACHE_DIR": "/tmp/flask-caching",
        },
    )


def setup_logging(app, gunicorn_logging=False):
    if gunicorn_logging:
        gunicorn_logger = logging.getLogger("gunicorn.error")
        app.logger.handlers = gunicorn_logger.handlers
        app.logger.setLevel(gunicorn_logger.level)


def setup_i18n(app):
    from flask import session

    babel.init_app(app)

    @babel.localeselector
    def get_locale():
        if request.args.get("lang"):
            session["lang"] = request.args["lang"]
        return session.get("lang", "fr")


def setup_csrf(app):
    csrf.init_app(app)

    @app.errorhandler(CSRFError)
    def bad_request(error):
        app.logger.warning(f"CSRF Error: {error}")
        return render_template("errors/400.html", error=error), 400


def setup_database(app):
    from .models import db

    db.init_app(app)
    Migrate(app, db, compare_type=True)


def setup_jinja(app):
    from b3desk.session import has_user_session
    from b3desk.session import get_current_user

    @app.context_processor
    def global_processor():
        if has_user_session():
            user = get_current_user()
            session_dict = {
                "user": user,
                "fullname": user.fullname,
            }
        else:
            session_dict = {
                "user": None,
                "fullname": "",
            }

        return {
            "config": app.config,
            "beta": app.config["BETA"],
            "documentation_link": app.config["DOCUMENTATION_LINK"],
            "is_rie": is_rie(),
            "version": "1.1.2",
            "LANGUAGES": LANGUAGES,
            **app.config["WORDINGS"],
            **session_dict,
        }


def setup_error_pages(app):
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(403)
    def not_authorized(error):
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template("errors/500.html", error=error), 500


def setup_endpoints(app):
    with app.app_context():
        import b3desk.routes

        app.register_blueprint(b3desk.routes.bp)


def create_app(test_config=None, gunicorn_logging=False):
    app = Flask(__name__)
    setup_configuration(app, test_config)
    setup_cache(app)
    setup_logging(app, gunicorn_logging)
    setup_i18n(app)
    setup_csrf(app)
    setup_database(app)
    setup_jinja(app)
    setup_error_pages(app)
    setup_endpoints(app)

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    return app

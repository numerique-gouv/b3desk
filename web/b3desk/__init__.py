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
import os
from logging.config import dictConfig

from flask import Flask
from flask import render_template
from flask import request
from flask import url_for
from flask_babel import Babel
from flask_caching import Cache
from flask_migrate import Migrate
from flask_pyoidc import OIDCAuthentication
from flask_wtf.csrf import CSRFError
from flask_wtf.csrf import CSRFProtect
from jinja2 import StrictUndefined

from b3desk.settings import MainSettings
from b3desk.utils import is_rie

from .utils import enum_converter
from .utils import model_converter

__version__ = "1.2.20dev"

LANGUAGES = ["en", "fr"]

babel = Babel()
cache = Cache()
csrf = CSRFProtect()
auth = OIDCAuthentication({"default": None, "attendee": None})
migrate = Migrate()


def setup_configuration(app, config=None):
    if config:
        app.config.from_mapping(config)

    config_obj = MainSettings.model_validate(config or {})
    app.config.from_object(config_obj)


def setup_celery(app):
    from b3desk.tasks import celery

    celery.conf.task_always_eager = app.testing


def setup_cache(app):
    if app.config.get("CACHE_TYPE"):
        config = None

    elif app.config.get("REDIS_URL"):
        host, port = app.config.get("REDIS_URL").split(":")
        config = {
            "CACHE_TYPE": "RedisCache",
            "CACHE_REDIS_HOST": host,
            "CACHE_REDIS_PORT": port,
        }

    else:
        config = {
            "CACHE_TYPE": "FileSystemCache",
            "CACHE_DIR": "/tmp/flask-caching",
        }

    cache.init_app(app, config=config)


def setup_sentry(app):  # pragma: no cover
    if not app.config.get("SENTRY_DSN"):
        return None

    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

    except Exception:
        return None

    sentry_sdk.init(dsn=app.config["SENTRY_DSN"], integrations=[FlaskIntegration()])
    return sentry_sdk


def setup_logging(app):
    if not app.debug and not app.testing:
        dictConfig(
            {
                "version": 1,
                "formatters": {
                    "default": {
                        "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
                    }
                },
                "handlers": {
                    "wsgi": {
                        "class": "logging.handlers.WatchedFileHandler",
                        "filename": "/var/log/b3desk.log",
                        "formatter": "default",
                    }
                },
                "root": {"level": "INFO", "handlers": ["wsgi"]},
            }
        )


def setup_i18n(app):
    from flask import session

    def locale_selector():
        if request.args.get("lang"):
            session["lang"] = request.args["lang"]
        return session.get("lang", "fr")

    babel.init_app(app, locale_selector=locale_selector)


def setup_csrf(app):
    csrf.init_app(app)

    @app.errorhandler(CSRFError)
    def bad_request(error):
        app.logger.warning(f"CSRF Error: {error}")
        return render_template("errors/400.html", error=error), 400


def setup_database(app):
    from .models import db

    db.init_app(app)
    migrate.init_app(app, db, compare_type=True)


def setup_jinja(app):
    from b3desk.models.roles import Role
    from b3desk.session import get_current_user
    from b3desk.session import has_user_session

    if app.debug or app.testing:
        app.jinja_env.undefined = StrictUndefined

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
            "development_version": __version__ == "0.0.0" or "dev" in __version__,
            "documentation_link": app.config["DOCUMENTATION_LINK"],
            "is_rie": is_rie(),
            "version": __version__,
            "LANGUAGES": LANGUAGES,
            "Role": Role,
            **app.config["WORDINGS"],
            **session_dict,
        }


def setup_flask(app):
    with app.app_context():
        from b3desk.models.meetings import Meeting
        from b3desk.models.roles import Role
        from b3desk.models.users import User

        for model in (Meeting, User):
            app.url_map.converters[model.__name__.lower()] = model_converter(model)

        for enum in (Role,):
            app.url_map.converters[enum.__name__.lower()] = enum_converter(enum)


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
        import b3desk.commands
        import b3desk.endpoints.api
        import b3desk.endpoints.join
        import b3desk.endpoints.meeting_files
        import b3desk.endpoints.meetings
        import b3desk.endpoints.public

        app.register_blueprint(b3desk.endpoints.public.bp)
        app.register_blueprint(b3desk.endpoints.join.bp)
        app.register_blueprint(b3desk.endpoints.meetings.bp)
        app.register_blueprint(b3desk.endpoints.api.bp)
        app.register_blueprint(b3desk.endpoints.meeting_files.bp)
        app.register_blueprint(b3desk.commands.bp)


def setup_oidc(app):
    from flask_pyoidc.provider_configuration import ClientMetadata
    from flask_pyoidc.provider_configuration import ProviderConfiguration

    with app.app_context():
        logout_url = url_for("public.logout", _external=True)

    user_provider_configuration = ProviderConfiguration(
        issuer=app.config["OIDC_ISSUER"],
        userinfo_http_method=app.config["OIDC_USERINFO_HTTP_METHOD"],
        client_metadata=ClientMetadata(
            client_id=app.config["OIDC_CLIENT_ID"],
            client_secret=app.config["OIDC_CLIENT_SECRET"],
            token_endpoint_auth_method=app.config["OIDC_CLIENT_AUTH_METHOD"],
            introspection_endpoint_auth_method=app.config[
                "OIDC_INTROSPECTION_AUTH_METHOD"
            ],
            post_logout_redirect_uris=[logout_url],
        ),
        auth_request_params={"scope": app.config["OIDC_SCOPES"]},
    )
    attendee_provider_configuration = ProviderConfiguration(
        issuer=app.config.get("OIDC_ATTENDEE_ISSUER"),
        userinfo_http_method=app.config.get("OIDC_ATTENDEE_USERINFO_HTTP_METHOD"),
        client_metadata=ClientMetadata(
            client_id=app.config.get("OIDC_ATTENDEE_CLIENT_ID"),
            client_secret=app.config.get("OIDC_ATTENDEE_CLIENT_SECRET"),
            token_endpoint_auth_method=app.config.get(
                "OIDC_ATTENDEE_CLIENT_AUTH_METHOD"
            ),
            introspection_endpoint_auth_method=app.config.get(
                "OIDC_ATTENDEE_INTROSPECTION_AUTH_METHOD"
            ),
            post_logout_redirect_uris=[logout_url],
        ),
        auth_request_params={"scope": app.config["OIDC_ATTENDEE_SCOPES"]},
    )

    # This is a hack to be able to initialize flask-oidc in two steps
    # https://github.com/zamzterz/Flask-pyoidc/issues/171
    auth._provider_configurations = {
        "default": user_provider_configuration,
        "attendee": attendee_provider_configuration,
    }
    auth.init_app(app)


def create_app(test_config=None):
    app = Flask(__name__)
    setup_configuration(app, test_config)
    sentry_sdk = setup_sentry(app)
    try:
        setup_celery(app)
        setup_cache(app)
        setup_logging(app)
        setup_i18n(app)
        setup_csrf(app)
        setup_database(app)
        setup_jinja(app)
        setup_flask(app)
        setup_error_pages(app)
        setup_endpoints(app)
        setup_oidc(app)
    except Exception as exc:  # pragma: no cover
        if sentry_sdk:
            sentry_sdk.capture_exception(exc)
        raise

    # ensure the instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    return app

import os

import arrow
import sentry_sdk
from flask import Flask, redirect, url_for, request
from flask_login import current_user
from sentry_sdk.integrations.flask import FlaskIntegration

from app.auth.base import auth_bp
from app.config import SCOPE_NAME, SCOPE_EMAIL, DB_URI, FLASK_SECRET, ENABLE_SENTRY
from app.dashboard.base import dashboard_bp
from app.developer.base import developer_bp
from app.extensions import db, login_manager
from app.log import LOG
from app.models import Client, User, Scope, ClientUser, GenEmail
from app.monitor.base import monitor_bp
from app.oauth.base import oauth_bp

if ENABLE_SENTRY:
    LOG.d("enable sentry")
    sentry_sdk.init(
        dsn="https://ad2187ed843340a1b4165bd8d5d6cdce@sentry.io/1478143",
        integrations=[FlaskIntegration()],
    )


def create_app() -> Flask:
    app = Flask(__name__)

    app.config["SQLALCHEMY_DATABASE_URI"] = DB_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.secret_key = FLASK_SECRET

    app.config["TEMPLATES_AUTO_RELOAD"] = True

    init_extensions(app)
    register_blueprints(app)
    set_index_page(app)
    jinja2_filter(app)

    return app


def fake_data():
    # Remove db if exist
    if os.path.exists("db.sqlite"):
        os.remove("db.sqlite")

    # Create all tables
    db.create_all()

    # fake data

    user = User.create(id=1, email="john@wick.com", name="John Wick")
    user.set_password("password")
    db.session.add(user)
    db.session.commit()

    client = Client.create(
        client_id="client-id",
        client_secret="client-secret",
        redirect_uri="http://sl-client:7000/callback",
        name="Continental",
        user_id=user.id,
    )
    db.session.add(client)

    scope_name = Scope.create(name=SCOPE_NAME)
    db.session.add(scope_name)
    scope_email = Scope.create(name=SCOPE_EMAIL)
    db.session.add(scope_email)
    db.session.commit()

    client.scopes.append(scope_name)
    client.scopes.append(scope_email)
    db.session.commit()

    gen_email = GenEmail.create(user_id=user.id, email="john-random@sl")
    db.session.commit()

    ClientUser.create(client_id=client.id, user_id=user.id, gen_email_id=gen_email.id)
    db.session.commit()


@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(user_id)

    return user


def register_blueprints(app: Flask):
    app.register_blueprint(auth_bp)
    app.register_blueprint(monitor_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(developer_bp)
    app.register_blueprint(oauth_bp)


def set_index_page(app):
    @app.route("/")
    def index():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
        else:
            return redirect(url_for("auth.login"))

    @app.before_request
    def before_request():
        LOG.debug(">>> Request %s", request.url)

    @app.after_request
    def after_request(res):
        LOG.debug("<<< Request ends %s", request.url)
        return res


def jinja2_filter(app):
    def format_datetime(value):
        dt = arrow.get(value)
        return dt.humanize()

    app.jinja_env.filters["dt"] = format_datetime


def init_extensions(app: Flask):
    LOG.debug("init extensions")
    login_manager.init_app(app)
    db.init_app(app)


if __name__ == "__main__":
    app = create_app()

    with app.app_context():
        fake_data()

    app.run(debug=True, threaded=False, host="0.0.0.0")

import os
from datetime import datetime

import arrow
import sentry_sdk
from flask import Flask, redirect, url_for, request, render_template
from flask_login import current_user
from sentry_sdk.integrations.flask import FlaskIntegration

from app.auth.base import auth_bp
from app.config import (
    SCOPE_NAME,
    SCOPE_EMAIL,
    DB_URI,
    FLASK_SECRET,
    ENABLE_SENTRY,
    ENV,
    URL,
)
from app.dashboard.base import dashboard_bp
from app.developer.base import developer_bp
from app.discover.base import discover_bp
from app.extensions import db, login_manager, migrate
from app.log import LOG
from app.models import Client, User, Scope, ClientUser, GenEmail, RedirectUri
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
    setup_error_page(app)
    setup_favicon_route(app)

    return app


def fake_data():
    # Remove db if exist
    if os.path.exists("db.sqlite"):
        os.remove("db.sqlite")

    # Create all tables
    db.create_all()

    # fake data
    Scope.create(name=SCOPE_NAME)
    Scope.create(name=SCOPE_EMAIL)
    db.session.commit()

    # Create a user
    user = User.create(id=1, email="john@wick.com", name="John Wick", activated=True)
    user.set_password("password")
    db.session.commit()

    # Create a client
    client1 = Client.create_new(name="Continental", user_id=user.id)
    client1.home_url = "http://sl-client:7000"
    client1.oauth_client_id = "client-id"
    client1.oauth_client_secret = "client-secret"
    client1.published = True
    db.session.commit()

    RedirectUri.create(client_id=client1.id, uri="http://sl-client:7000/callback")
    RedirectUri.create(client_id=client1.id, uri="http://localhost:7000/callback")
    db.session.commit()

    # Create another client
    client2 = Client.create_new(name="Rome", user_id=user.id)
    db.session.commit()

    gen_email = GenEmail.create(user_id=user.id, email="john-random@sl")
    GenEmail.create(user_id=user.id, email="john-random-2@sl")
    db.session.commit()

    ClientUser.create(client_id=client1.id, user_id=user.id, gen_email_id=gen_email.id)
    ClientUser.create(client_id=client2.id, user_id=user.id)
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
    app.register_blueprint(discover_bp)


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


def setup_error_page(app):
    @app.errorhandler(400)
    def page_not_found(e):
        return render_template("error/400.html"), 400

    @app.errorhandler(401)
    def page_not_found(e):
        return render_template("error/401.html"), 401

    @app.errorhandler(403)
    def page_not_found(e):
        return render_template("error/403.html"), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template("error/404.html"), 404


def setup_favicon_route(app):
    @app.route("/favicon.ico")
    def favicon():
        return redirect("/static/favicon.ico")


def jinja2_filter(app):
    def format_datetime(value):
        dt = arrow.get(value)
        return dt.humanize()

    app.jinja_env.filters["dt"] = format_datetime

    @app.context_processor
    def inject_stage_and_region():
        return dict(YEAR=datetime.now().year, URL=URL, ENABLE_SENTRY=ENABLE_SENTRY)


def init_extensions(app: Flask):
    LOG.debug("init extensions")
    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app)


if __name__ == "__main__":
    app = create_app()

    if ENV == "local":
        LOG.d("reset db, add fake data")
        with app.app_context():
            fake_data()

    app.run(debug=True, threaded=False, host="0.0.0.0")

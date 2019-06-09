from IPython import embed
from sqlalchemy_utils import create_database, database_exists, drop_database

from app.config import DB_URI, SCOPE_NAME, SCOPE_EMAIL
from app.extensions import db
from app.log import LOG
from app.models import Scope
from server import create_app


def create_db():
    if not database_exists(DB_URI):
        LOG.debug("db not exist, create database")
        create_database(DB_URI)

    app = create_app()

    with app.app_context():
        # Create all tables
        db.create_all()


def drop_db():
    drop_database(DB_URI)


def prepare_db():
    app = create_app()

    with app.app_context():
        scope_name = Scope.create(name=SCOPE_NAME)
        db.session.add(scope_name)
        scope_email = Scope.create(name=SCOPE_EMAIL)
        db.session.add(scope_email)
        db.session.commit()


embed()

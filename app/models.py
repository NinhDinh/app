# <<< Models >>>
from datetime import datetime

import bcrypt
from flask_login import UserMixin

from app.extensions import db


class ModelMixin(object):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=None, onupdate=datetime.utcnow)


class User(db.Model, ModelMixin, UserMixin):
    email = db.Column(db.String(128), unique=True, nullable=False)
    salt = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(128))

    def set_password(self, password):
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode(), salt).decode()
        self.salt = salt.decode()
        self.password = password_hash

    def check_password(self, password) -> bool:
        password_hash = bcrypt.hashpw(password.encode(), self.salt.encode())
        return self.password.encode() == password_hash


# <<< OAUTH models >>>


class Client(db.Model, ModelMixin):
    client_id = db.Column(db.String(128), unique=True, nullable=False)
    client_secret = db.Column(db.String(128), nullable=False)

    redirect_uri = db.Column(db.String(1024))
    name = db.Column(db.String(128))

    # user who created this client
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)


class AuthorizationCode(db.Model, ModelMixin):
    code = db.Column(db.String(128), unique=True, nullable=False)
    client_id = db.Column(db.ForeignKey(Client.id), nullable=False)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)


class OauthToken(db.Model, ModelMixin):
    access_token = db.Column(db.String(128), unique=True)
    client_id = db.Column(db.ForeignKey(Client.id), nullable=False)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)

    user = db.relationship(User)

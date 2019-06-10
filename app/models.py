import hashlib
from datetime import datetime

import bcrypt
from flask_login import UserMixin

from app.extensions import db


class ModelMixin(object):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=None, onupdate=datetime.utcnow)

    _repr_hide = ["created_at", "updated_at"]

    @classmethod
    def query(cls):
        return db.session.query(cls)

    @classmethod
    def get(cls, id):
        return cls.query.get(id)

    @classmethod
    def get_by(cls, **kw):
        return cls.query.filter_by(**kw).first()

    @classmethod
    def filter_by(cls, **kw):
        return cls.query.filter_by(**kw)

    @classmethod
    def get_or_create(cls, **kw):
        r = cls.get_by(**kw)
        if not r:
            r = cls(**kw)
            db.session.add(r)

        return r

    @classmethod
    def create(cls, **kw):
        r = cls(**kw)
        db.session.add(r)
        return r

    def save(self):
        db.session.add(self)

    def delete(self):
        db.session.delete(self)

    def __repr__(self):
        values = ", ".join(
            "%s=%r" % (n, getattr(self, n))
            for n in self.__table__.c.keys()
            if n not in self._repr_hide
        )
        return "%s(%s)" % (self.__class__.__name__, values)


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

    def gravatar_url(self):
        hash_email = hashlib.md5(self.email.encode("utf-8")).hexdigest()
        return f"https://www.gravatar.com/avatar/{hash_email}"


# <<< OAUTH models >>>

client_scope = db.Table(
    "client_scope",
    db.Column("client_id", db.Integer, db.ForeignKey("client.id"), primary_key=True),
    db.Column("scope_id", db.Integer, db.ForeignKey("scope.id"), primary_key=True),
)


class Client(db.Model, ModelMixin):
    client_id = db.Column(db.String(128), unique=True, nullable=False)
    client_secret = db.Column(db.String(128), nullable=False)

    redirect_uri = db.Column(db.String(1024))
    name = db.Column(db.String(128))

    # user who created this client
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)

    scopes = db.relationship("Scope", secondary=client_scope, lazy="subquery")


class AuthorizationCode(db.Model, ModelMixin):
    code = db.Column(db.String(128), unique=True, nullable=False)
    client_id = db.Column(db.ForeignKey(Client.id), nullable=False)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)

    user = db.relationship(User, lazy=False)
    client = db.relationship(Client, lazy=False)


class OauthToken(db.Model, ModelMixin):
    access_token = db.Column(db.String(128), unique=True)
    client_id = db.Column(db.ForeignKey(Client.id), nullable=False)
    user_id = db.Column(db.ForeignKey(User.id), nullable=False)

    user = db.relationship(User)
    client = db.relationship(Client)


class Scope(db.Model, ModelMixin):
    name = db.Column(db.String(128), unique=True)


class GenEmail(db.Model, ModelMixin):
    """Generated email"""

    user_id = db.Column(db.ForeignKey(User.id), nullable=False)
    email = db.Column(db.String(128), unique=True)


class ClientUser(db.Model, ModelMixin):
    __table_args__ = (
        db.UniqueConstraint("user_id", "client_id", name="uq_client_user"),
    )

    user_id = db.Column(db.ForeignKey(User.id), nullable=False)
    client_id = db.Column(db.ForeignKey(Client.id), nullable=False)

    # Null means client has access to user original email
    gen_email_id = db.Column(db.ForeignKey(GenEmail.id), nullable=True)

    gen_email = db.relationship(GenEmail)

    user = db.relationship(User)
    client = db.relationship(Client)

    def get_email(self):
        return self.gen_email.email if self.gen_email_id else self.user.email

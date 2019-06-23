import enum
import hashlib

import arrow
import bcrypt
from flask_login import UserMixin
from sqlalchemy_utils import ArrowType

from app import s3
from app.config import SCOPE_NAME, SCOPE_EMAIL, URL
from app.extensions import db
from app.log import LOG
from app.utils import convert_to_id, random_string


class ModelMixin(object):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(ArrowType, default=arrow.utcnow, nullable=False)
    updated_at = db.Column(ArrowType, default=None, onupdate=arrow.utcnow)

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


class PlanEnum(enum.Enum):
    free = 0
    trial = 1
    monthly = 2
    yearly = 3


class User(db.Model, ModelMixin, UserMixin):
    __tablename__ = "users"
    email = db.Column(db.String(128), unique=True, nullable=False)
    salt = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

    activated = db.Column(db.Boolean, default=False, nullable=False)

    plan = db.Column(
        db.Enum(PlanEnum),
        nullable=False,
        default=PlanEnum.free,
        server_default=PlanEnum.free.name,
    )

    # only relevant for trial period
    plan_expiration = db.Column(ArrowType)

    stripe_customer_id = db.Column(db.String(128), unique=True)
    stripe_card_token = db.Column(db.String(128), unique=True)
    stripe_subscription_id = db.Column(db.String(128), unique=True)

    def should_upgrade(self):
        return self.plan in (PlanEnum.free, PlanEnum.trial)

    def is_premium(self):
        return self.plan in (PlanEnum.monthly, PlanEnum.yearly)

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


class ActivationCode(db.Model, ModelMixin):
    """For activate user account"""

    user_id = db.Column(db.ForeignKey(User.id, ondelete="cascade"), nullable=False)
    code = db.Column(db.String(128), unique=True, nullable=False)

    user = db.relationship(User)


class File(db.Model, ModelMixin):
    path = db.Column(db.String(128), unique=True, nullable=False)

    def get_url(self):
        return s3.get_url(self.path)


# <<< OAUTH models >>>

client_scope = db.Table(
    "client_scope",
    db.Column(
        "client_id",
        db.Integer,
        db.ForeignKey("client.id", ondelete="cascade"),
        primary_key=True,
        nullable=False,
    ),
    db.Column(
        "scope_id",
        db.Integer,
        db.ForeignKey("scope.id", ondelete="cascade"),
        primary_key=True,
        nullable=False,
    ),
)


def generate_oauth_client_id(client_name) -> str:
    oauth_client_id = convert_to_id(client_name) + "-" + random_string()

    # check that the client does not exist yet
    if not Client.get_by(oauth_client_id=oauth_client_id):
        LOG.debug("generate oauth_client_id %s", oauth_client_id)
        return oauth_client_id

    # Rerun the function
    LOG.warning(
        "client_id %s already exists, generate a new client_id", oauth_client_id
    )
    return generate_oauth_client_id(client_name)


class Client(db.Model, ModelMixin):
    oauth_client_id = db.Column(db.String(128), unique=True, nullable=False)
    oauth_client_secret = db.Column(db.String(128), nullable=False)

    name = db.Column(db.String(128), nullable=False)
    home_url = db.Column(db.String(1024))
    published = db.Column(db.Boolean, default=False, nullable=False)

    # user who created this client
    user_id = db.Column(db.ForeignKey(User.id, ondelete="cascade"), nullable=False)
    icon_id = db.Column(db.ForeignKey(File.id), nullable=True)

    scopes = db.relationship("Scope", secondary=client_scope, lazy="subquery")
    icon = db.relationship(File)

    def nb_user(self):
        return ClientUser.filter_by(client_id=self.id).count()

    @classmethod
    def create_new(cls, name, user_id) -> "Client":
        # generate a client-id
        oauth_client_id = generate_oauth_client_id(name)
        oauth_client_secret = random_string(40)
        client = Client.create(
            name=name,
            oauth_client_id=oauth_client_id,
            oauth_client_secret=oauth_client_secret,
            user_id=user_id,
        )

        # By default, add email and name scope
        client.scopes.append(Scope.get_by(name=SCOPE_NAME))
        client.scopes.append(Scope.get_by(name=SCOPE_EMAIL))

        return client

    def get_icon_url(self):
        if self.icon_id:
            return self.icon.get_url()
        else:
            return URL + "/static/default-icon.svg"


class RedirectUri(db.Model, ModelMixin):
    """Valid redirect uris for a client"""

    client_id = db.Column(db.ForeignKey(Client.id, ondelete="cascade"), nullable=False)
    uri = db.Column(db.String(1024), nullable=False)

    client = db.relationship(Client, backref="redirect_uris")


class AuthorizationCode(db.Model, ModelMixin):
    code = db.Column(db.String(128), unique=True, nullable=False)
    client_id = db.Column(db.ForeignKey(Client.id, ondelete="cascade"), nullable=False)
    user_id = db.Column(db.ForeignKey(User.id, ondelete="cascade"), nullable=False)

    user = db.relationship(User, lazy=False)
    client = db.relationship(Client, lazy=False)


class OauthToken(db.Model, ModelMixin):
    access_token = db.Column(db.String(128), unique=True)
    client_id = db.Column(db.ForeignKey(Client.id, ondelete="cascade"), nullable=False)
    user_id = db.Column(db.ForeignKey(User.id, ondelete="cascade"), nullable=False)

    user = db.relationship(User)
    client = db.relationship(Client)


class Scope(db.Model, ModelMixin):
    name = db.Column(db.String(128), unique=True, nullable=False)


class GenEmail(db.Model, ModelMixin):
    """Generated email"""

    user_id = db.Column(db.ForeignKey(User.id, ondelete="cascade"), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=False)

    enabled = db.Column(db.Boolean(), default=True, nullable=False)

    def __repr__(self):
        return f"<GenEmail {self.id} {self.email}>"


class ClientUser(db.Model, ModelMixin):
    __table_args__ = (
        db.UniqueConstraint("user_id", "client_id", name="uq_client_user"),
    )

    user_id = db.Column(db.ForeignKey(User.id, ondelete="cascade"), nullable=False)
    client_id = db.Column(db.ForeignKey(Client.id, ondelete="cascade"), nullable=False)

    # Null means client has access to user original email
    gen_email_id = db.Column(
        db.ForeignKey(GenEmail.id, ondelete="cascade"), nullable=True
    )

    gen_email = db.relationship(GenEmail, backref="client_users")

    user = db.relationship(User)
    client = db.relationship(Client)

    def get_email(self):
        return self.gen_email.email if self.gen_email_id else self.user.email

    def get_user_info(self) -> dict:
        """return user info according to client scope
        Return dict with key being scope name

        """
        res = {"id": self.id, "client": self.client.name}

        for scope in self.client.scopes:
            if scope.name == SCOPE_NAME:
                res[SCOPE_NAME] = self.user.name
            elif scope.name == SCOPE_EMAIL:
                # Use generated email
                if self.gen_email_id:
                    LOG.debug(
                        "Use gen email for user %s, client %s", self.user, self.client
                    )
                    res[SCOPE_EMAIL] = self.gen_email.email
                # Use user original email
                else:
                    res[SCOPE_EMAIL] = self.user.email

        return res

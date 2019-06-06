from flask import request, render_template, redirect, url_for
from flask_login import current_user, login_required
from wtforms import Form, StringField, validators

from app.developer.base import developer_bp
from app.extensions import db
from app.log import LOG
from app.models import Client
from app.utils import random_string, convert_to_id


class NewClientForm(Form):
    name = StringField("Name", validators=[validators.DataRequired()])
    redirect_uri = StringField("Redirect URI", validators=[validators.DataRequired()])


def generate_client_id(client_name) -> str:
    client_id = convert_to_id(client_name) + "-" + random_string()

    # check that the client does not exist yet
    if not Client.get_by(client_id=client_id):
        LOG.debug("generate client_id %s", client_id)
        return client_id

    # Rerun the function
    LOG.warning("client_id %s already exists, generate a new client_id", client_id)
    return generate_client_id(client_name)


@developer_bp.route("/new_client", methods=["GET", "POST"])
@login_required
def new_client():
    form = NewClientForm(request.form)

    if request.method == "POST":
        if form.validate():
            # generate a client-id
            client_id = generate_client_id(form.name.data)
            client_secret = random_string(40)

            Client.create(
                name=form.name.data,
                redirect_uri=form.redirect_uri.data,
                client_id=client_id,
                client_secret=client_secret,
                user_id=current_user.id,
            )

            db.session.commit()

            return redirect(url_for("developer.index"))

    return render_template("developer/new_client.html", form=form)

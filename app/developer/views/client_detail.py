from flask import request, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms import StringField, validators

from app.developer.base import developer_bp
from app.extensions import db
from app.models import Client, RedirectUri


class EditClientForm(FlaskForm):
    name = StringField("Name", validators=[validators.DataRequired()])


@developer_bp.route("/clients/<client_id>", methods=["GET", "POST"])
@login_required
def client_detail(client_id):
    client = Client.get(client_id)
    if not client:
        flash("no such client", "warning")
        return redirect(url_for("developer.index"))

    if client.user_id != current_user.id:
        flash("you cannot see this client", "warning")
        return redirect(url_for("developer.index"))

    if request.method == "GET":
        form = EditClientForm(name=client.name)
    else:
        form = EditClientForm(request.form)

        if form.validate():
            client.name = form.name.data

            uris = request.form.getlist("uri")

            # replace all uris. TODO: optimize this?
            for redirect_uri in client.redirect_uris:
                redirect_uri.delete()

            for uri in uris:
                RedirectUri.create(client_id=client_id, uri=uri)

            db.session.commit()

            flash(f"client {client.name} has been updated", "success")

            return redirect(url_for("developer.client_detail", client_id=client.id))

    return render_template("developer/client_detail.html", form=form, client=client)

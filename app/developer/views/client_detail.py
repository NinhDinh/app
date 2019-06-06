from flask import request, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from wtforms import Form, StringField, validators

from app.developer.base import developer_bp
from app.extensions import db
from app.models import Client


class EditClientForm(Form):
    name = StringField("Name", validators=[validators.DataRequired()])
    redirect_uri = StringField("Redirect URI", validators=[validators.DataRequired()])


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
        form = EditClientForm(name=client.name, redirect_uri=client.redirect_uri)
    else:
        form = EditClientForm(request.form)

        if form.validate():

            client.name = form.name.data
            client.redirect_uri = form.redirect_uri.data

            db.session.commit()

            flash(f"client {client.name} has been updated successfully")

            return redirect(url_for("developer.index"))

    return render_template("developer/client_detail.html", form=form, client=client)

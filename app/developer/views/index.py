"""List of clients"""
from flask import render_template, request, flash
from flask_login import current_user, login_required

from app.developer.base import developer_bp
from app.extensions import db
from app.models import Client


@developer_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    # delete client
    if request.method == "POST":
        client_id = int(request.form.get("client-id"))
        client = Client.get(client_id)

        if client.user_id != current_user.id:
            flash("You cannot remove this client", "warning")
        else:
            client_name = client.name
            client.delete()
            db.session.commit()
            flash(f"Client {client_name} has been deleted successfully", "success")

    clients = Client.filter_by(user_id=current_user.id).all()

    return render_template("developer/index.html", clients=clients)

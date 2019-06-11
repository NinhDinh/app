from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app.dashboard.base import dashboard_bp
from app.extensions import db
from app.log import LOG
from app.models import GenEmail, ClientUser
from app.oauth.views.authorize import generate_email


@dashboard_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    # User generates a new email
    if request.method == "POST":
        random_email = generate_email()
        GenEmail.create(user_id=current_user.id, email=random_email)
        db.session.commit()

        LOG.d("generate new email %s for user %s", random_email, current_user)

        return redirect(url_for("dashboard.index"))

    client_users = (
        ClientUser.filter_by(user_id=current_user.id)
        .options(joinedload(ClientUser.client))
        .options(joinedload(ClientUser.gen_email))
        .all()
    )

    used_gen_email_ids = [client_user.gen_email_id for client_user in client_users]

    # Emails not used by any client
    gen_emails = (
        GenEmail.query.filter(GenEmail.id.notin_(used_gen_email_ids))
        .filter(GenEmail.user_id == current_user.id)
        .all()
    )

    return render_template(
        "dashboard/index.html", client_users=client_users, gen_emails=gen_emails
    )

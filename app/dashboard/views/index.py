from flask import render_template
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app.dashboard.base import dashboard_bp
from app.models import ClientUser


@dashboard_bp.route("/")
@login_required
def index():
    client_users = (
        ClientUser.filter_by(user_id=current_user.id)
        .options(joinedload(ClientUser.client))
        .options(joinedload(ClientUser.gen_email))
        .all()
    )

    return render_template("dashboard/index.html", client_users=client_users)

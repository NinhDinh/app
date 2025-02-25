from flask import request, flash, render_template, redirect, url_for
from flask_login import login_user

from app.auth.base import auth_bp
from app.extensions import db
from app.models import EmailChange


@auth_bp.route("/change_email", methods=["GET", "POST"])
def change_email():
    code = request.args.get("code")

    email_change: EmailChange = EmailChange.get_by(code=code)

    if not email_change:
        return render_template("auth/change_email.html", incorrect_code=True)

    if email_change.is_expired():
        return render_template("auth/change_email.html", expired_code=True)

    user = email_change.user
    user.email = email_change.new_email

    EmailChange.delete(email_change.id)
    db.session.commit()

    flash("Your new email has been updated successfully", "success")

    login_user(user)

    return redirect(url_for("dashboard.index"))

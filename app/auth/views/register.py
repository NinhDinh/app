from flask import request, flash, render_template, redirect, url_for
from flask_login import login_user
from wtforms import StringField, validators

from app.auth.base import auth_bp
from app.extensions import db
from app.form import BaseForm
from app.log import LOG
from app.models import User


class RegisterForm(BaseForm):
    email = StringField("Email", validators=[validators.DataRequired()])
    password = StringField(
        "Password", validators=[validators.DataRequired(), validators.Length(min=8)]
    )
    name = StringField("Name", validators=[validators.DataRequired()])


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST":
        if form.validate():
            user = User.query.filter_by(email=form.email.data).first()

            if user:
                flash(f"Email {form.email.data} already exists", "warning")
                return render_template("auth/register.html", form=form)

            LOG.debug("create user %s", form.email.data)
            user = User(email=form.email.data, name=form.name.data)
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            login_user(user)

            return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html", form=form)

import urllib.parse

from flask import request, flash, render_template
from flask_wtf import FlaskForm
from wtforms import StringField, validators

from app import email_utils
from app.auth.base import auth_bp
from app.config import URL
from app.extensions import db
from app.log import LOG
from app.models import User, ActivationCode
from app.utils import random_string


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[validators.DataRequired()])
    password = StringField(
        "Password", validators=[validators.DataRequired(), validators.Length(min=8)]
    )
    name = StringField("Name", validators=[validators.DataRequired()])


def encode_url(url):
    return urllib.parse.quote(url, safe="")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST":
        if form.validate():
            user = User.filter_by(email=form.email.data).first()

            if user:
                flash(f"Email {form.email.data} already exists", "warning")
                return render_template("auth/register.html", form=form)

            LOG.debug("create user %s", form.email.data)
            user = User.create(email=form.email.data, name=form.name.data)
            user.set_password(form.password.data)
            db.session.commit()

            activation = ActivationCode.create(user_id=user.id, code=random_string(30))
            db.session.commit()

            # Send user activation email
            activation_link = f"{URL}/auth/activate?code={activation.code}"
            if "next" in request.args:
                LOG.d("redirect user to %s after activation", request.args["next"])
                activation_link = (
                    activation_link + "&next=" + encode_url(request.args["next"])
                )

            email_utils.send(
                user.email,
                "Welcome to SimpleLogin! Confirm your email",
                html_content=f"""
Welcome to SimpleLogin {user.name}! <br><br>                
                
            
You're on your way! <br><br>
Let's confirm your email address. <br><br>

By clicking on the following <a href="{activation_link}">link</a>, you are confirming your email address. <br><br>

Or you can paste this link into your browser: <br><br>
{activation_link} <br><br>

See you very soon! <br>
Son - SimpleLogin Founder.<br>
            
            """,
            )

            return render_template("auth/register_waiting_activation.html")

    return render_template("auth/register.html", form=form)

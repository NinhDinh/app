from flask import render_template, request
from flask_login import login_required
from flask_wtf import FlaskForm
from wtforms import StringField, validators

from app.dashboard.base import dashboard_bp


class SettingForm(FlaskForm):
    name = StringField("Name", validators=[validators.DataRequired()])


@dashboard_bp.route("/setting", methods=["GET", "POST"])
@login_required
def setting():
    form = SettingForm(request.form)

    return render_template("dashboard/setting.html", form=form)

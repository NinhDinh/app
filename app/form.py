from datetime import timedelta

from flask_wtf import Form
from wtforms.csrf.session import SessionCSRF


class BaseForm(Form):
    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = b"TODO"
        csrf_time_limit = timedelta(minutes=20)

from datetime import timedelta

from flask import session
from wtforms import Form
from wtforms.csrf.session import SessionCSRF


class BaseForm(Form):
    class Meta:
        csrf = True
        csrf_class = SessionCSRF
        csrf_secret = b"TODO"
        csrf_time_limit = timedelta(minutes=20)

        @property
        def csrf_context(self):
            return session

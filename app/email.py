# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import SUPPORT_EMAIL, SENDGRID_API_KEY
from app.log import LOG


def send(to_email, subject, html_content):
    message = Mail(
        from_email=SUPPORT_EMAIL,
        to_emails=to_email,
        subject=subject,
        html_content=html_content,
    )
    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)
    LOG.d("sendgrid res:%s", response.status_code)

# using SendGrid's Python Library
# https://github.com/sendgrid/sendgrid-python
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.config import SUPPORT_EMAIL, SENDGRID_API_KEY, EMAIL_DOMAIN
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


def notify_admin(subject, html_content):
    """only works when there's a postfix server running locally"""
    msg = MIMEMultipart("alternative")

    fromaddr = f"noreply@{EMAIL_DOMAIN}"
    toaddr = SUPPORT_EMAIL

    msg["From"] = fromaddr
    msg["To"] = toaddr
    msg["Subject"] = subject

    msg.attach(
        MIMEText(
            f"""<html><body>
    {html_content}
    </body></html>""",
            "html",
        )
    )

    with smtplib.SMTP(host="localhost") as server:
        server.sendmail(fromaddr, toaddr, msg.as_string())

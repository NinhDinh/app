import os
import subprocess

from dotenv import load_dotenv

SHA1 = subprocess.getoutput("git rev-parse HEAD")

config_file = os.environ.get("CONFIG")
if config_file:
    print("load config file", config_file)
    load_dotenv(config_file)
else:
    load_dotenv()

SCOPE_NAME = "name"
SCOPE_EMAIL = "email"

URL = os.environ.get("URL") or "http://sl-server:5000"
EMAIL_DOMAIN = os.environ.get("EMAIL_DOMAIN") or "sl"
SUPPORT_EMAIL = os.environ.get("SUPPORT_EMAIL") or "support@sl"
SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
DB_URI = os.environ.get("DB_URI") or "sqlite:///db.sqlite"

FLASK_SECRET = os.environ.get("FLASK_SECRET") or "secret"

# invalidate the session at each new version by changing the secret
FLASK_SECRET = FLASK_SECRET + SHA1

ENABLE_SENTRY = "ENABLE_SENTRY" in os.environ
ENV = os.environ.get("ENV") or "local"

print("email domain is", EMAIL_DOMAIN)


AWS_REGION = "eu-west-3"
BUCKET = os.environ.get("BUCKET") or "local.sl"
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

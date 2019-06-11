import os

from dotenv import load_dotenv

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
ENABLE_SENTRY = "ENABLE_SENTRY" in os.environ
ENV = os.environ.get("ENV") or "local"

print("email domain is", EMAIL_DOMAIN)

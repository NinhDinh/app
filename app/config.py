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


EMAIL_DOMAIN = os.environ.get("EMAIL_DOMAIN") or "sl"
DB_URI = os.environ.get("DB_URI") or "sqlite:///db.sqlite"
FLASK_SECRET = os.environ.get("FLASK_SECRET") or "secret"
ENABLE_SENTRY = "ENABLE_SENTRY" in os.environ
ENV = os.environ.get("ENV") or "local"

print("email domain is", EMAIL_DOMAIN)

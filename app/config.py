import os

SCOPE_NAME = "name"
SCOPE_EMAIL = "email"

EMAIL_DOMAIN = os.environ.get("EMAIL_DOMAIN") or "sl"

print("email domain is", EMAIL_DOMAIN)

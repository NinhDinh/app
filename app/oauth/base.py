from flask import Blueprint

oauth_bp = Blueprint(name="oauth", import_name=__name__, url_prefix="/oauth")

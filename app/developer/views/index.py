"""List of clients"""
from flask import render_template

from app.developer.base import developer_bp


@developer_bp.route("/")
def index():
    return render_template("developer/index.html")

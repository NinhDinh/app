from flask import request, jsonify

from app.models import OauthToken
from app.oauth.base import oauth_bp


@oauth_bp.route("/user_info")
def user_info():
    """
    Call by client to get user information
    Usually bearer token is used.
    """
    access_token = request.headers["AUTHORIZATION"].replace("Bearer ", "")
    oauth_token = OauthToken.get_by(access_token=access_token)
    if not oauth_token:
        return jsonify(error="Need bearer token"), 400

    user = oauth_token.user

    return jsonify({"email": user.email, "name": user.name})

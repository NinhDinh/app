from flask import request, jsonify

from app.models import OauthToken, ClientUser
from app.oauth.base import oauth_bp


@oauth_bp.route("/user_info")
def user_info():
    """
    Call by client to get user information
    Usually bearer token is used.
    """
    access_token = request.headers["AUTHORIZATION"].replace("Bearer ", "")
    oauth_token: OauthToken = OauthToken.get_by(access_token=access_token)
    if not oauth_token:
        return jsonify(error="Need bearer token"), 400

    client_user = ClientUser.get_or_create(
        client_id=oauth_token.client_id, user_id=oauth_token.user_id
    )

    return jsonify(client_user.get_user_info())

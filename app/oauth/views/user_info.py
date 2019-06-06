from flask import request, jsonify

from app.config import SCOPE_NAME, SCOPE_EMAIL
from app.models import OauthToken
from app.oauth.base import oauth_bp


def get_user_info(user, client) -> dict:
    """return user info according to client scope"""
    res = {}
    for scope in client.scopes:
        if scope.name == SCOPE_NAME:
            res[SCOPE_NAME] = user.name
        elif scope.name == SCOPE_EMAIL:
            res[SCOPE_EMAIL] = user.email

    return res


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

    return jsonify(get_user_info(oauth_token.user, oauth_token.client))

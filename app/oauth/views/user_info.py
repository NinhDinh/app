from flask import request, jsonify

from app.config import SCOPE_NAME, SCOPE_EMAIL
from app.log import LOG
from app.models import OauthToken, ClientUser
from app.oauth.base import oauth_bp


def get_user_info(user, client) -> dict:
    """return user info according to client scope"""

    client_user: ClientUser = ClientUser.get_by(client_id=client.id, user_id=user.id)
    if not client_user:
        raise Exception("client cannot access user data")

    res = {}
    for scope in client.scopes:
        if scope.name == SCOPE_NAME:
            res[SCOPE_NAME] = user.name
        elif scope.name == SCOPE_EMAIL:
            # Use generated email
            if client_user.gen_email_id:
                LOG.debug("Use gen email for user %s, client %s", user, client)
                res[SCOPE_EMAIL] = client_user.gen_email.email
            # Use user original email
            else:
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

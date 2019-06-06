from flask import request, render_template, redirect, url_for, session
from flask_login import current_user, login_required

from app.extensions import db
from app.log import LOG
from app.models import Client, AuthorizationCode
from app.oauth.base import oauth_bp
from app.utils import random_string


@oauth_bp.route("/authorize")
def authorize():
    """
    Redirected from client when user clicks on "Login with Server".
    This is a GET request with the following field in url
    - client_id
    - (optional) state
    - response_type: must be code
    """
    client_id = request.args.get("client_id")
    state = request.args.get("state")
    response_type = request.args.get("response_type")

    # sanity check
    if not response_type == "code":
        return "response_type must be code", 400

    client = Client.get_by(client_id=client_id)
    if not client:
        return f"no such client with id {client_id}", 400

    if current_user.is_authenticated:
        return render_template(
            "oauth/authorize_login_user.html", client=client, state=state
        )
    else:
        # after user logs in, redirect user back to this page
        session["redirect_after_login"] = request.url

        return redirect(url_for("auth.login"))


@oauth_bp.route("/allow-deny", methods=["POST"])
@login_required
def allow_client():
    """
    This page handles the POST request when user clicks on "Allow" or "Deny" on the authorization page.
    At this point, user must be logged in.
    Once user approves, this will redirect user back to client with the authorization code and state.
    :return:
    """
    client_id = request.form.get("client-id")
    client = Client.get(client_id)
    state = request.form.get("state")

    if request.form.get("button") == "allow":
        LOG.debug("User %s allows Client %s", current_user, client)

        # Create authorization code
        auth_code = AuthorizationCode(
            client_id=client.id, user_id=current_user.id, code=random_string()
        )
        db.session.add(auth_code)
        db.session.commit()

        redirect_url = f"{client.redirect_uri}?code={auth_code.code}&state={state}"
        return redirect(redirect_url)
    else:
        LOG.debug("User %s denies Client %s", current_user, client)
        redirect_url = f"{client.redirect_uri}?error=deny&state={state}"
        return redirect(redirect_url)

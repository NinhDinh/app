from urllib.parse import urlparse

from flask import request, render_template, redirect
from flask_login import current_user, login_required

from app.config import EMAIL_DOMAIN
from app.extensions import db
from app.log import LOG
from app.models import Client, AuthorizationCode, ClientUser, GenEmail, RedirectUri
from app.oauth.base import oauth_bp
from app.utils import random_string


def get_host_name_and_scheme(url: str) -> (str, str):
    """http://localhost:5000?a=b -> (localhost, http) """
    url_comp = urlparse(url)

    return url_comp.hostname, url_comp.scheme


@oauth_bp.route("/authorize")
def authorize():
    """
    Redirected from client when user clicks on "Login with Server".
    This is a GET request with the following field in url
    - client_id
    - (optional) state
    - response_type: must be code
    """
    oauth_client_id = request.args.get("client_id")
    state = request.args.get("state")
    response_type = request.args.get("response_type")
    redirect_uri: str = request.args.get("redirect_uri")

    # sanity check
    if not response_type == "code":
        LOG.d("incorrect response_type %s", response_type)
        return "response_type must be code", 400

    if not redirect_uri:
        LOG.d("no redirect uri")
        return "redirect_uri must be set", 400

    client = Client.get_by(oauth_client_id=oauth_client_id)
    if not client:
        return f"no such client with oauth-client-id {oauth_client_id}", 400

    # check if redirect_uri is valid
    # allow localhost by default
    if not redirect_uri.startswith("http://localhost"):
        if not RedirectUri.get_by(client_id=client.id, uri=redirect_uri):
            return f"{redirect_uri} is not authorized"

    if current_user.is_authenticated:
        # user has already allowed this client
        client_user: ClientUser = ClientUser.get_by(
            client_id=client.id, user_id=current_user.id
        )
        if client_user:
            LOG.debug("user %s has already allowed client %s", current_user, client)
            user_info = client_user.get_user_info()

            return render_template(
                "oauth/already_authorize.html",
                client=client,
                state=state,
                redirect_uri=redirect_uri,
                user_info=user_info,
            )
        else:
            return render_template(
                "oauth/authorize_login_user.html",
                client=client,
                state=state,
                redirect_uri=redirect_uri,
            )
    else:
        # after user logs in, redirect user back to this page
        return render_template(
            "oauth/authorize_nonlogin_user.html",
            client=client,
            state=state,
            next=request.url,
        )


def generate_email() -> str:
    random_email = random_string(20) + "@" + EMAIL_DOMAIN

    # check that the client does not exist yet
    if not GenEmail.get_by(email=random_email):
        LOG.debug("generate email %s", random_email)
        return random_email

    # Rerun the function
    LOG.warning("email %s already exists, generate a new email", random_email)
    return generate_email()


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
    redirect_uri = request.form.get("redirect-uri")

    gen_new_email = request.form.get("gen-email") == "on"

    if request.form.get("button") == "allow":
        LOG.debug("User %s allows Client %s", current_user, client)

        # Create authorization code
        auth_code = AuthorizationCode.create(
            client_id=client.id, user_id=current_user.id, code=random_string()
        )
        db.session.add(auth_code)
        db.session.commit()

        client_user = ClientUser.get_or_create(
            client_id=client.id, user_id=current_user.id
        )
        db.session.commit()

        if gen_new_email:
            random_email = generate_email()
            gen_email = GenEmail.create(user_id=current_user.id, email=random_email)
            db.session.commit()
            LOG.debug(
                "generate email %s for user %s, client %s",
                random_email,
                current_user,
                client,
            )

            client_user.gen_email_id = gen_email.id
            db.session.commit()

        redirect_url = f"{redirect_uri}?code={auth_code.code}&state={state}"
        return redirect(redirect_url)
    else:
        LOG.debug("User %s denies Client %s", current_user, client)
        redirect_url = f"{redirect_uri}?error=deny&state={state}"
        return redirect(redirect_url)

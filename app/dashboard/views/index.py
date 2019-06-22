import arrow
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from app import email_utils
from app.config import MAX_NB_EMAIL_FREE_PLAN
from app.dashboard.base import dashboard_bp
from app.extensions import db
from app.log import LOG
from app.models import GenEmail, ClientUser, PlanEnum
from app.oauth.views.authorize import generate_email


@dashboard_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    # User generates a new email
    if request.method == "POST":
        if request.form.get("form-name") == "trigger-email":
            gen_email_id = request.form.get("gen-email-id")
            gen_email = GenEmail.get(gen_email_id)

            LOG.d("trigger an email to %s", gen_email)
            email_utils.send(
                gen_email.email,
                "A Test Email",
                f"""
Hi {current_user.name} ! <br><br>
This is a test email to make sure you receive email sent at {gen_email.email} <br><br>
If you have any question, feel free to reply to this email :) <br><br>
Have a nice day <br><br>
SimpleLogin team.
            """,
            )
            flash(
                f"An email sent to {gen_email.email} is on its way, please check your inbox/spam folder",
                "success",
            )

        elif request.form.get("form-name") == "create-new-email":
            can_create_new_email = True

            if current_user.plan != PlanEnum.free:
                if current_user.plan_expiration <= arrow.now() and (
                    GenEmail.filter_by(user_id=current_user.id).count()
                    >= MAX_NB_EMAIL_FREE_PLAN
                ):
                    flash(
                        f"You need to extend your plan to create new email. "
                        f"Your current plan is expired {current_user.plan_expiration.humanize()}",
                        "warning",
                    )

                    can_create_new_email = False

            else:  # free plan
                if (
                    GenEmail.filter_by(user_id=current_user.id).count()
                    >= MAX_NB_EMAIL_FREE_PLAN
                ):
                    flash(
                        f"You need to upgrade your plan to create new email.", "warning"
                    )

                    can_create_new_email = False

            if can_create_new_email:
                random_email = generate_email()
                GenEmail.create(user_id=current_user.id, email=random_email)
                db.session.commit()

                LOG.d("generate new email %s for user %s", random_email, current_user)
                flash(f"Email {random_email} has been created", "success")

        elif request.form.get("form-name") == "switch-email-forwarding":
            gen_email_id = request.form.get("gen-email-id")
            gen_email: GenEmail = GenEmail.get(gen_email_id)

            LOG.d("switch email forwarding for %s", gen_email)

            gen_email.enabled = not gen_email.enabled
            if gen_email.enabled:
                flash(
                    f"The email forwarding for {gen_email.email} has been enabled",
                    "success",
                )
            else:
                flash(
                    f"The email forwarding for {gen_email.email} has been disabled",
                    "warning",
                )
            db.session.commit()

        return redirect(url_for("dashboard.index"))

    client_users = (
        ClientUser.filter_by(user_id=current_user.id)
        .options(joinedload(ClientUser.client))
        .options(joinedload(ClientUser.gen_email))
        .all()
    )

    sorted(client_users, key=lambda cu: cu.client.name)

    gen_emails = (
        GenEmail.filter_by(user_id=current_user.id)
        .order_by(GenEmail.email)
        .options(joinedload(GenEmail.client_users))
        .all()
    )

    return render_template(
        "dashboard/index.html", client_users=client_users, gen_emails=gen_emails
    )

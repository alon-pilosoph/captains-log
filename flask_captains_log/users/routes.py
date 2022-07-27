from flask_captains_log import db, bcrypt
from flask_captains_log.models import User
from flask_captains_log.users.forms import (
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
    RequestResetForm,
)
from flask_captains_log.users.helpers import send_password_reset_email
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

# Initialize Blueprint
users = Blueprint("users", __name__)


@users.route("/register", methods=["GET", "POST"])
def register():
    """View to handle user registration"""

    # Make sure user isn't logged in
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    # Create WTForm to register user
    form = RegistrationForm()
    # If form validated, hash password and create user in db
    if form.validate_on_submit():
        email = form.email.data
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash("Your account has been created.", "success")
        # Redirect to login page
        return redirect(url_for("users.login"))

    # If page was reached by GET method, render page with registration form
    return render_template("register.html", form=form)


@users.route("/login", methods=["GET", "POST"])
def login():
    """View to handle user login"""

    # Make sure user isn't logged in
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    # Create WTForm to login user
    form = LoginForm()
    # If form validated, try to login
    if form.validate_on_submit():
        # Get form data
        email = form.email.data
        password = form.password.data
        remember = form.remember.data
        user = User.query.filter_by(email=email).first()
        # If credentials are correct, log user in
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=remember)
            flash("You logged in successfully.", "success")
            # Get next page to redirect after login
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            # If there is no next page, redirect to index
            return redirect(url_for("main.index"))
        # If credentials aren't correct, redirect with flash message
        else:
            flash("Login unsuccessful. Please check your credentials.", "danger")

    # If page was reached by GET method, render page with login form
    return render_template("login.html", form=form)


@users.route("/logout")
def logout():
    """View to handle user logout"""
    logout_user()
    return redirect(url_for("main.index"))


@users.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    """View to handle requests to reset password"""

    # Make sure user isn't logged in
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    # Create WTForm to submit reset requests
    form = RequestResetForm()
    # If form validated, send reset link to user's email
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_password_reset_email(user)
        flash(
            "An email has been sent with instructions to reset your password.", "info"
        )
        return redirect(url_for("users.login"))

    # If page was reached by GET method, render page with reset request form
    return render_template("reset_request.html", form=form)


@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """View to handle password reset.
    Token is passed as route variable and verified in view."""

    # Make sure user isn't logged in
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    # Get user that is associated with token
    user = User.verify_reset_token(token)
    # If token is invalid or expired
    if user is None:
        flash("The password reset link is invalid or has expired.", "danger")
        return redirect(url_for("users.login"))
    # Otherwise, create WTForm to reset password
    form = ResetPasswordForm()
    # If form validated, hash password and update in db
    if form.validate_on_submit():
        user.password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        db.session.commit()
        flash("Your password has been updated.", "success")
        return redirect(url_for("users.login"))

    # If page was reached by GET method, render page with reset form
    return render_template("reset_password.html", form=form)

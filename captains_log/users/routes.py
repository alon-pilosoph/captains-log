from captains_log import bcrypt, db
from captains_log.models import User
from captains_log.users.forms import (
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
    RequestResetForm,
)
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
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash("Your account has been created.", "success")
        # Login registered user
        login_user(user)
        # Redirect to home page
        return redirect(url_for("main.index"))

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
        # Verify user's credentials
        user = User.verify_credentials(form.email.data, form.password.data)
        # If credentials are correct, login user
        if user:
            login_user(user, remember=form.remember.data)
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
        user.send_password_reset_email()
        flash(
            "An email has been sent with instructions to reset your password.",
            "success",
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
    # If form validated, hash password, reset current token and update in db
    if form.validate_on_submit():
        user.password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user.reset_token = None
        db.session.commit()
        flash("Your password has been updated.", "success")
        return redirect(url_for("users.login"))

    # If page was reached by GET method, render page with reset form
    return render_template("reset_password.html", form=form)

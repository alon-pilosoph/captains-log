from flask_captains_log import mail
from flask import render_template, url_for
from flask_mail import Message


def send_password_reset_email(user):
    """Helper method that accepts a User object and sends a password reset link to that user's email"""
    token = user.get_reset_token()
    msg = Message(
        "Password Reset Request",
        sender="alon.pilosoph@gmail.com",
        recipients=[user.email],
    )
    msg.html = render_template(
        "reset_email.html",
        password_reset_url=url_for("users.reset_password", token=token, _external=True),
    )
    mail.send(msg)

from flask_captains_log.models import User
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    EmailField,
    PasswordField,
    SubmitField,
    ValidationError,
    validators,
)


class RegistrationForm(FlaskForm):
    """WTForm class to register users"""

    email = EmailField(
        "Email",
        [validators.DataRequired(), validators.Email()],
        render_kw={"autofocus": True},
    )
    password = PasswordField(
        "Password",
        [
            validators.DataRequired(),
            validators.Length(min=5, max=20),
            validators.Regexp(
                r"(?=.*\d)(?=.*[a-z])(?=.*[A-Z])",
                message="Password must include at least one number, one uppercase and one lowercase character.",
            ),
        ],
    )
    confirm = PasswordField(
        "Confirm Password",
        [
            validators.DataRequired(),
            validators.EqualTo("password", message="Passwords do not match."),
        ],
    )
    submit = SubmitField("Register")

    def validate_email(self, email):
        """Custom validator to make sure email address is not already in db"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("This email address is already registered.")


class LoginForm(FlaskForm):
    """WTForm class to log users in"""

    email = EmailField(
        "Email",
        [validators.DataRequired(), validators.Email()],
        render_kw={"autofocus": True},
    )
    password = PasswordField("Password", [validators.DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log In")


class RequestResetForm(FlaskForm):
    """WTForm class to send password reset emails"""

    email = EmailField(
        "Email",
        [validators.DataRequired(), validators.Email()],
        render_kw={"autofocus": True},
    )
    submit = SubmitField("Send Reset Email")

    def validate_email(self, email):
        """Custom validator to make sure email address is in db"""
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError(
                "There is no account with the provided email address."
            )


class ResetPasswordForm(FlaskForm):
    """WTForm class to reset password"""

    password = PasswordField(
        "New Password",
        [
            validators.DataRequired(),
            validators.Length(min=5, max=20),
            validators.Regexp(
                r"(?=.*\d)(?=.*[a-z])(?=.*[A-Z])",
                message="Password must include at least one number, one uppercase and one lowercase character.",
            ),
        ],
    )
    confirm = PasswordField(
        "Confirm Password",
        [
            validators.DataRequired(),
            validators.EqualTo("password", message="Passwords do not match."),
        ],
    )
    submit = SubmitField("Set Password")

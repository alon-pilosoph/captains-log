import captains_log.constants as constants
from captains_log import bcrypt, db, login_manager, mail
from flask import current_app, render_template, url_for
from flask_login import UserMixin
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer
from random import choice


@login_manager.user_loader
def load_user(user_id):
    """Method for Flask login manager"""
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    """Model that represents users"""

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    # Columns that represent the current state of the user
    current_planet_id = db.Column(
        db.Integer,
        db.ForeignKey("planet.id", use_alter=True, name="fk_current_planet_id"),
        default=None,
    )
    current_discovery_id = db.Column(
        db.Integer,
        db.ForeignKey("discovery.id", use_alter=True, name="fk_current_discovery_id"),
        default=None,
    )
    reset_token = db.Column(db.String(100), default=None)
    # Relationships
    current_planet = db.relationship(
        "Planet",
        foreign_keys=[current_planet_id],
    )
    current_discovery = db.relationship(
        "Discovery",
        foreign_keys=[current_discovery_id],
    )
    # Planets associated with user
    planets = db.relationship(
        "Planet",
        foreign_keys="[Planet.user_id]",
        back_populates="explorer",
        cascade="all, delete",
        lazy=True,
    )

    @staticmethod
    def verify_credentials(email, password):
        """Static method that verifies user credentials"""

        # Query the database for user by given email
        user = User.query.filter_by(email=email).first()
        # Verify user exists in db and that the given password matches (short-cirtcuit condition)
        if user and bcrypt.check_password_hash(user.password, password):
            return user
        return False

    def send_password_reset_email(self):
        """Method that sends a reset email to the user.
        The email contains a URL with a timed token associated with the user."""

        password_reset_serializer = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"]
        )
        token = password_reset_serializer.dumps(self.id, salt="password-reset-salt")
        # Store most recent reset token in db
        self.reset_token = token
        db.session.commit()
        msg = Message("Password Reset Request", recipients=[self.email])
        msg.html = render_template(
            "reset_email.html",
            password_reset_url=url_for(
                "users.reset_password", token=token, _external=True
            ),
        )
        mail.send(msg)

    @staticmethod
    def verify_reset_token(token):
        """Static method to verify timed token to reset password.
        If verified, the method returns the relevant user object."""

        password_reset_serializer = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"]
        )
        try:
            # Try to load user id from token
            # Maximum age of token is 1 hour
            user_id = password_reset_serializer.loads(
                token, salt="password-reset-salt", max_age=3600
            )
        except:
            # If token not validated, return None
            return None
        # Query for user by id loaded from token
        user = User.query.get(user_id)
        # If user's current reset token is the token received, return user
        if user.reset_token == token:
            return user
        # Otherwise, return None
        return None

    def __repr__(self):
        return f"<User id={self.id}, email={self.email}>"


class Planet(db.Model):
    """Model that represents discovered planets"""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), default="Unnamed Planet")
    things_to_discover = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # Relationships
    # User associated with planet
    explorer = db.relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="planets",
        lazy=True,
    )
    # Discoveries associated with planet
    discoveries = db.relationship(
        "Discovery",
        foreign_keys="[Discovery.planet_id]",
        back_populates="planet",
        cascade="all, delete",
        lazy=True,
    )

    def generate_prompt(self):
        circumstances = choice(constants.CIRCUMSTANCES)
        while True:
            thing_discovered = (
                f"{choice(constants.CATEGORIES)} {choice(constants.LOCATIONS)}"
            )
            if not Discovery.query.filter_by(
                planet_id=self.id,
                thing_discovered=thing_discovered,
            ).first():
                break

        return circumstances, thing_discovered

    def __repr__(self):
        return f"<Planet id={self.id}, name={self.name}, things_to_discover={self.things_to_discover}>"


class Discovery(db.Model):
    """Model that represents discoveries"""

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    circumstances = db.Column(db.String(40), nullable=False)
    thing_discovered = db.Column(db.String(70), nullable=False)
    description = db.Column(db.Text)
    planet_id = db.Column(db.Integer, db.ForeignKey("planet.id"), nullable=False)
    # Relationships
    # Planet associated with discovery
    planet = db.relationship(
        "Planet",
        foreign_keys=[planet_id],
        back_populates="discoveries",
        lazy=True,
    )

    def __repr__(self):
        return f"<Discovery id={self.id}, planet_id={self.planet_id}>"

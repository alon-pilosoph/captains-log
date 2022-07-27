import flask_captains_log.constants as constants
from flask_captains_log import db, login_manager
from flask import current_app
from flask_login import UserMixin
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
    # Columns that represent state of user
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

    def get_reset_token(self):
        """Method that returns a timed token associated with user to send in reset email"""
        password_reset_serializer = URLSafeTimedSerializer(
            current_app.config["SECRET_KEY"]
        )
        return password_reset_serializer.dumps(self.id, salt="password-reset-salt")

    @staticmethod
    def verify_reset_token(token):
        """Method to verify timed token to reset password.
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
        return User.query.get(user_id)

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

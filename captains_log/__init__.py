from captains_log.config import Config
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions without associating to app
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "users.login"
login_manager.login_message_category = "info"
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    # Configure app from Config class
    app.config.from_object(Config)
    # Associate extensions to app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    # Import blueprints
    from captains_log.main.routes import main
    from captains_log.users.routes import users
    from captains_log.discoveries.routes import discoveries
    from captains_log.errors.handlers import errors

    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(users)
    app.register_blueprint(discoveries)
    app.register_blueprint(errors)

    return app

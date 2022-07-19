import os

alchemy_uri = os.environ.get("DATABASE_URL")
if alchemy_uri.startswith("postgres://"):
    alchemy_uri = alchemy_uri.replace("postgres://", "postgresql://", 1)


class Config:
    """Class to handle app configuration"""

    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = alchemy_uri
    MAIL_SERVER = "smtp.googlemail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    EMAIL_USERNAME = os.environ.get("EMAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("EMAIL_PASS")

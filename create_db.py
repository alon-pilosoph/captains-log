from run import app
from captains_log import db

# Create db in heroku
with app.app_context():
    db.create_all()

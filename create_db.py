from run import app
from flask_captains_log import db

# Create db on heroku
with app.app_context():
    db.create_all()

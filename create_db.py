from run import app
from captains_log import db

# Create db on heroku
with app.app_context():
    db.create_all()

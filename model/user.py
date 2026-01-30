from app import db
from datetime import date

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    email = db.Column(db.String(128), unique=True)
    password = db.Column(db.String(255))
    role = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    create_at = db.Column(db.Date, default=date.today)

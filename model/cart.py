from app import db
from datetime import date

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    create_at = db.Column(db.Date, default=date.today)

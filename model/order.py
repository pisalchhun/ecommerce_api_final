from app import db
from datetime import date

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    total_amount = db.Column(db.Float)
    status = db.Column(db.String(50))  
    payment_method = db.Column(db.String(50))
    shipping_address = db.Column(db.String(255))
    create_at = db.Column(db.Date, default=date.today)
    items = db.relationship('OrderItem', backref='order', lazy=True)

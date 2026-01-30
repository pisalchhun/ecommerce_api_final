from app import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    name = db.Column(db.String(128))
    stock = db.Column(db.Integer)
    price =db.Column(db.Float)
    description = db.Column(db.String(255))
    image = db.Column(db.String(255))
    create_at = db.Column(db.Date)
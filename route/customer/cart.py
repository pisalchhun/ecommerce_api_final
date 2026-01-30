from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request
from sqlalchemy import text
from datetime import date
from app import app, db
from model.order import Order
from model.order_Item import OrderItem
from model.product import Product

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return fn(*args, **kwargs)
        except Exception:
            return jsonify({
                "error": "Login required",
                "redirect": "/login"
            }), 401
    return wrapper

@app.get('/api/cart')
@login_required
def get_all_carts():
    sql = text("""
        SELECT o.id AS cart_id,
               o.user_id,
               u.name AS user_name,
               oi.product_id,
               p.name AS product_name,
               oi.quantity,
               oi.price,
               (oi.quantity * oi.price) AS total
        FROM "order" o
        JOIN order_item oi ON o.id = oi.order_id
        JOIN product p ON oi.product_id = p.id
        JOIN "user" u ON o.user_id = u.id
        WHERE o.status = 'Cart'
        ORDER BY o.user_id, o.id
    """)
    result = db.session.execute(sql).fetchall()
    if not result:
        return jsonify({'message': 'No carts found'})

    rows = [dict(row._mapping) for row in result]
    return jsonify(rows)

@app.get('/api/cart/user/<int:user_id>')
@login_required
def get_cart(user_id):
    sql = text("""
        SELECT o.id AS cart_id,
               o.user_id,
               oi.product_id,
               p.name AS product_name,
               oi.quantity,
               oi.price,
               (oi.quantity * oi.price) AS total
        FROM "order" o
        JOIN order_item oi ON o.id = oi.order_id
        JOIN product p ON oi.product_id = p.id
        WHERE o.user_id = :user_id AND o.status = 'Cart'
    """)
    result = db.session.execute(sql, {'user_id': user_id}).fetchall()
    if not result:
        return jsonify({'message': 'Cart is empty'})

    rows = [dict(row._mapping) for row in result]
    return jsonify(rows)

@app.post('/api/cart/add')
@login_required
def add_to_cart():
    data = request.get_json()
    required = ['user_id', 'product_id', 'quantity']

    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    product = Product.query.get(data['product_id'])
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    cart = Order.query.filter_by(user_id=data['user_id'], status='Cart').first()
    if not cart:
        sql = text("""
            INSERT INTO "order" (user_id, total_amount, status, create_at)
            VALUES (:user_id, 0, 'Cart', :create_at)
            RETURNING id
        """)
        result = db.session.execute(sql, {
            'user_id': data['user_id'],
            'create_at': date.today()
        })
        cart_id = result.fetchone()[0]
    else:
        cart_id = cart.id
    existing_item = db.session.execute(
        text("SELECT * FROM order_item WHERE order_id = :order_id AND product_id = :product_id"),
        {'order_id': cart_id, 'product_id': data['product_id']}
    ).fetchone()

    if existing_item:

        db.session.execute(
            text("UPDATE order_item SET quantity = quantity + :qty WHERE order_id = :order_id AND product_id = :product_id"),
            {'qty': data['quantity'], 'order_id': cart_id, 'product_id': data['product_id']}
        )
    else:

        db.session.execute(
            text("INSERT INTO order_item (order_id, product_id, quantity, price) VALUES (:order_id, :product_id, :quantity, :price)"),
            {'order_id': cart_id, 'product_id': data['product_id'], 'quantity': data['quantity'], 'price': product.price}
        )

    db.session.execute(
        text("UPDATE \"order\" SET total_amount = (SELECT SUM(quantity * price) FROM order_item WHERE order_id = :order_id) WHERE id = :order_id"),
        {'order_id': cart_id}
    )

    db.session.commit()
    return jsonify({'message': 'Item added to cart', 'cart_id': cart_id})

@app.put('/api/cart/update')
@login_required
def update_cart_item():
    data = request.get_json()
    required = ['user_id', 'product_id', 'quantity']

    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    cart = Order.query.filter_by(user_id=data['user_id'], status='Cart').first()
    if not cart:
        return jsonify({'error': 'Cart not found'}), 404

    db.session.execute(
        text("UPDATE order_item SET quantity = :quantity WHERE order_id = :order_id AND product_id = :product_id"),
        {'quantity': data['quantity'], 'order_id': cart.id, 'product_id': data['product_id']}
    )

    db.session.execute(
        text("UPDATE \"order\" SET total_amount = (SELECT SUM(quantity * price) FROM order_item WHERE order_id = :order_id) WHERE id = :order_id"),
        {'order_id': cart.id}
    )

    db.session.commit()
    return jsonify({'message': 'Cart item updated'})
@app.delete('/api/cart/remove')
@login_required
def remove_cart_item():
    data = request.get_json()
    required = ['user_id', 'product_id']

    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    cart = Order.query.filter_by(user_id=data['user_id'], status='Cart').first()
    if not cart:
        return jsonify({'error': 'Cart not found'}), 404

    db.session.execute(
        text("DELETE FROM order_item WHERE order_id = :order_id AND product_id = :product_id"),
        {'order_id': cart.id, 'product_id': data['product_id']}
    )

    db.session.execute(
        text("UPDATE \"order\" SET total_amount = (SELECT COALESCE(SUM(quantity * price), 0) FROM order_item WHERE order_id = :order_id) WHERE id = :order_id"),
        {'order_id': cart.id}
    )

    db.session.commit()
    return jsonify({'message': 'Item removed from cart'})

@app.delete('/api/cart/clear/<int:user_id>')
@login_required
def clear_cart(user_id):
    cart = Order.query.filter_by(user_id=user_id, status='Cart').first()
    if not cart:
        return jsonify({'error': 'Cart not found'}), 404

    db.session.execute(text("DELETE FROM order_item WHERE order_id = :order_id"), {'order_id': cart.id})
    db.session.execute(text("UPDATE \"order\" SET total_amount = 0 WHERE id = :order_id"), {'order_id': cart.id})
    db.session.commit()
    return jsonify({'message': 'Cart cleared successfully'})

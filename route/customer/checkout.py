from functools import wraps

from flask import jsonify, request
from flask_jwt_extended import verify_jwt_in_request
from sqlalchemy import text
from datetime import date
from app import app, db
from model.order import Order

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
            })
    return wrapper

@app.get('/api/checkout')
@login_required
def get_orders():
    sql = text("""
        SELECT o.id,
               o.user_id,
               u.name AS customer_name,
               o.total_amount,
               o.status,
               o.payment_method,
               o.shipping_address,
               o.create_at
        FROM "order" o
        JOIN "user" u ON o.user_id = u.id
        ORDER BY o.create_at DESC
    """)
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    return jsonify(rows) if rows else jsonify({'message': 'No orders found'})

@app.get('/api/checkout/<int:id>')
@login_required
def get_order_by_id(id):
    sql = text("""
        SELECT o.*,
               u.name AS customer_name
        FROM "order" o
        JOIN "user" u ON o.user_id = u.id
        WHERE o.id = :id
    """)
    result = db.session.execute(sql, {'id': id}).fetchone()

    if not result:
        return jsonify({'error': 'Order not found'}), 404

    return jsonify(dict(result._mapping))

@app.post('/api/checkout/create')
@login_required
def create_order():
    data = request.get_json()
    required = ['user_id', 'total_amount', 'payment_method', 'shipping_address']

    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        sql = text("""
            INSERT INTO "order"
            (user_id, total_amount, status, payment_method, shipping_address, create_at)
            VALUES
            (:user_id, :total_amount, :status, :payment_method, :shipping_address, :create_at)
        """)

        db.session.execute(sql, {
            "user_id": data['user_id'],
            "total_amount": float(data['total_amount']),
            "status": data.get('status', 'Pending'),
            "payment_method": data['payment_method'],
            "shipping_address": data['shipping_address'],
            "create_at": date.today()
        })
        db.session.commit()

        return jsonify({'message': 'Order created successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.put('/api/checkout/update-status')
@login_required
def update_order_status():
    data = request.get_json()
    order_id = data.get('order_id')
    new_status = data.get('status')

    if not order_id or not new_status:
        return jsonify({'error': 'order_id and status are required'}), 400

    sql = text('UPDATE "order" SET status = :status WHERE id = :id')
    db.session.execute(sql, {'status': new_status, 'id': order_id})
    db.session.commit()

    return jsonify({'message': f'Order {order_id} updated to {new_status}'})

@app.delete('/api/checkout/delete')
@login_required
def delete_order():
    data = request.get_json()
    order_id = data.get('order_id')

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': f'Order id = {order_id} not found'})

    db.session.execute(
        text('DELETE FROM "order" WHERE id = :id'),
        {'id': order_id}
    )
    db.session.commit()

    return jsonify({'message': 'Order deleted successfully'})

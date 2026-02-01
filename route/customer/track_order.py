from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app import app
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
            }), 401
    return wrapper
@app.get('/api/track-orders/<int:order_id>')
@login_required
def track_order(order_id):
    order = Order.query.filter_by(id=order_id).first()
    if not order:
        return jsonify({'error': f'Order id {order_id} not found'}), 404

    order_data = {
        "id": order.id,
        "user_id": order.user_id,
        "total_amount": order.total_amount,
        "status": order.status,
        "payment_method": order.payment_method if order.payment_method else "Not set",
        "shipping_address": order.shipping_address if order.shipping_address else "Not set",
        "create_at": order.create_at.strftime("%Y-%m-%d"),
        "items": [
            {
                "product_name": item.product.name,
                "quantity": item.quantity,
                "price": item.price
            } for item in order.items
        ],
        "status_history": [
            {
                "status": sh.status,
                "updated_at": sh.created_at.strftime("%Y-%m-%d")
            } for sh in sorted(order.status_history, key=lambda x: x.created_at)
        ]
    }

    return jsonify(order_data), 200

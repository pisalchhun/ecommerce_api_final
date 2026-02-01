import re
from flask import request
from werkzeug.security import generate_password_hash
from sqlalchemy import text
from app import app, db
from model.user import User
from flask import jsonify
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt()
        if claims.get("role") != "admin":
            return jsonify({"message": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper

def is_valid_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def fetch_user_by_id(user_id: int):
    sql = text("""
        SELECT id,
               UPPER(name) AS name,
               'true' AS active,
               email,
               role,
               create_at
        FROM user
        WHERE id = :user_id
    """)
    result = db.session.execute(sql, {"user_id": user_id}).fetchone()
    if not result:
        return None
    return dict(result._mapping)

@app.get('/api/admin/users')
@admin_required
def get_user():
    sql = text("""
        SELECT id,
               UPPER(name) AS name,
               'true' AS active,
               email,
               role,
               create_at
        FROM user
    """)
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]

    if not rows:
        return jsonify({'message': 'No users found'})

    return jsonify(rows)

@app.get('/api/admin/users/list')
@admin_required
def get_all_users():
    sql = text("""
        SELECT id,
               UPPER(name) AS name,
               'true' AS active,
               email,
               role,
               create_at
        FROM user
    """)
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]

    return jsonify(rows)

@app.get('/api/admin/users/list/<int:user_id>')
@admin_required
def get_user_id(user_id: int):
    user = fetch_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'})
    return jsonify(user)

@app.post('/api/admin/users/create')
@admin_required
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Request body is required'})

    name = data.get('name')
    password = data.get('password')
    email = data.get('email')
    role = data.get('role', 'user')

    if not name:
        return jsonify({'error': 'No user name provided'})
    if not password:
        return jsonify({'error': 'No password provided'})
    if not email or not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'})

    new_user = User(
        name=name,
        password=generate_password_hash(password),
        email=email,
        role=role
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'message': 'User created successfully',
        'user': {
            'id': new_user.id,
            'name': new_user.name,
            'email': new_user.email,
            'role': new_user.role
        }
    })

@app.put('/api/admin/users/update/<int:id>')
@admin_required
def update_user(id):
    user = User.query.get(id)
    if not user:
        return jsonify({'error': 'User not found'}), 404

    data = request.get_json(silent=True) or {}

    name = (data.get('name') or '').strip()
    password = data.get('password')
    email = (data.get('email') or '').strip()
    role = data.get('role')

    if not name:
        return jsonify({'error': 'No user name provided'}), 400
    if not password:
        return jsonify({'error': 'No password provided'}), 400
    if not email or not is_valid_email(email):
        return jsonify({'error': 'Invalid email format'}), 400

    user.name = name
    user.password = generate_password_hash(password)
    user.email = email
    user.role = role

    db.session.commit()

    return jsonify({'message': 'User updated successfully'})

@app.delete('/api/admin/users/delete')
@admin_required
def delete_user():
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'error': 'user_id is required'})

    user_id = data['user_id']
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message': 'User not found'})

    db.session.delete(user)
    db.session.commit()

    return jsonify({
        'message': 'User deleted successfully',
        'deleted_user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        }
    })

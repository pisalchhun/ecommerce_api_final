from datetime import datetime
from app import app, db
from flask import jsonify, request
from sqlalchemy import text
from model.category import Category
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
@app.get('/api/category')
@admin_required
def get_category():
    sql = text("SELECT id,  UPPER(SUBSTR(name, 1, 1)) || LOWER(SUBSTR(name, 2)) AS name, 'true' as active,create_at FROM category")
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    if not rows:
        return jsonify({'message': 'No category found'})
    return jsonify(rows)

@app.get('/api/category/list')
@admin_required
def get_all_category():
    sql = text("SELECT id,  UPPER(SUBSTR(name, 1, 1)) || LOWER(SUBSTR(name, 2)) AS name, 'true' as active,create_at FROM category")
    result = db.session.execute(sql).fetchall()
    rows = [dict(row._mapping) for row in result]
    if not rows:
        return jsonify({'message': 'No category found'})
    return jsonify(rows)

@app.get('/api/category/list/<int:id>')
def get_category_by_id(id):
    category = Category.query.get_or_404(id)
    return jsonify({
        'id': category.id,
        'name': category.name,
        'active': "true",
        'create_at': category.create_at,
    })


def sql_fetch(category_id: int):
    sql = text("SELECT id,  UPPER(SUBSTR(name, 1, 1)) || LOWER(SUBSTR(name, 2)) AS name, create_at FROM category WHERE id = :id")
    result = db.session.execute(sql, {"id": category_id}).fetchone()
    if not result:
        return None
    return dict(result._mapping)

@app.post('/api/category/create')
@admin_required
def add_category():
    data = request.get_json()
    if 'name' not in data:
        return jsonify({"error": "Missing key 'name'"})

    if not data['name'].strip():
        return jsonify({"error": "Name cannot be empty"})

    new_category = Category(
        name=data['name'],
        create_at=datetime.now(),
    )
    db.session.add(new_category)
    db.session.commit()
    add_category = sql_fetch(new_category.id)


    return jsonify({
        'message': 'Category created successfully',
        'category': add_category
    })


@app.put('/api/category/update')
@admin_required
def update_category():
    data = request.get_json()
    category_id = data.get('category_id')
    if not category_id:
        return jsonify(
            {
                'error': 'Category ID is required'
            }
        )
    category = Category.query.get(category_id)

    if not category:
        return jsonify({'error': 'Category not found'})

    new_name = data.get('name')
    if not new_name:
        return jsonify({'error': "Missing key 'name' in request"})
    create_at = datetime.now()
    formatted_date = create_at.strftime("%Y-%m-%d")
    display_date = create_at.strftime("%d-%m-%Y")
    category.name = new_name
    category.created_at = formatted_date
    db.session.commit()
    category_info = {
        'id': category_id,
        'name': category.name,
        'active': "true",
        'create_at': display_date,

    }
    return jsonify({
        'message': 'Category updated successfully',
        'category': category_info
    })


@app.delete('/api/category/delete')
@admin_required
def delete_category():
    data = request.get_json()
    category_id = data.get('category_id')
    if not category_id:
        return jsonify({'error': 'Category ID is required'})
    category = Category.query.get_or_404(category_id)
    create_at = datetime.now()
    display_date = create_at.strftime("%d-%m-%Y")
    db.session.delete(category)
    db.session.commit()
    category_info = {
        'id': category.id,
        'name': category.name,
        'active': "true",
        'create_at': display_date,

    }
    return jsonify({
        'message': 'Category deleted successfully',
        'Category': category_info
    })


import uuid
from datetime import datetime
from app import app, db
from flask import request
from sqlalchemy import text
from model.product import Product
from werkzeug.utils import secure_filename
import os
from flask import jsonify

from route.admin.required import admin_required

def get_full_image_url(image_path):
    if not image_path:
        return None
    return request.host_url.rstrip('/') + image_path

UPLOAD_FOLDER = 'static/image'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.get('/api/products')
@app.get('/api/products/list')
def get_products():
    sql = text("""
        SELECT p.id,
               UPPER(SUBSTR(p.name, 1, 1)) || LOWER(SUBSTR(p.name, 2)) AS product_name,
               p.price,
               p.stock,
               p.description,
               p.image,
               c.name AS category_name,
               p.create_at
        FROM product AS p
        LEFT JOIN category AS c ON p.category_id = c.id
    """)

    result = db.session.execute(sql).fetchall()

    rows = []
    total_price = 0
    total_stock = 0
    categories = set()

    for row in result:
        r = dict(row._mapping)
        r['image'] = get_full_image_url(r['image']) if r['image'] else None

        total_price += r['price']
        total_stock += r['stock']
        if r['category_name']:
            categories.add(r['category_name'])

        rows.append(r)

    return jsonify({
        "products": rows if rows else [{"msg": "Product not found"}]
    })


@app.get('/api/products/list/<int:id>')
def get_product_by_id(id):
    sql = text("""
        SELECT p.id, UPPER(SUBSTR(p.name, 1, 1)) || LOWER(SUBSTR(p.name, 2)) as product_name, 'true' as active, 
               '$' || p.price AS price, p.stock, p.description, 
               p.image, c.name as category_name
        FROM product AS p
        JOIN category AS c ON p.category_id = c.id
        WHERE p.id = :id
    """)
    result = db.session.execute(sql, {'id': id}).fetchall()
    if not result:
        return jsonify({'error': 'Product not found'})

    rows = []
    for row in result:
        r = dict(row._mapping)
        r['image'] = get_full_image_url(r['image'])
        rows.append(r)

    return jsonify(rows)

@app.post('/api/admin/products/create')
@admin_required
def create_products():
    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock')
    description = data.get('description')
    category_id = data.get('category_id')
    image_url = data.get('image')
    create_at = datetime.now()
    formatted_date = create_at.strftime("%Y-%m-%d")
    display_date = create_at.strftime("%d-%m-%Y")

    if not name: return {'error': 'No product name provided'}
    if not price: return {'error': 'No price provided'}
    if not stock: return {'error': 'No stock provided'}
    if not category_id: return {'error': 'No category_id provided'}

    try:
        price = float(price)
        stock = int(stock)
        category_id = int(category_id)
    except ValueError:
        return {'error': 'Invalid numeric value'}

    if 'image_url' in request.files:
        image = request.files['image_url']
        if image and allowed_file(image.filename):
            filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(file_path)
            image_url = f"/static/image/{filename}"
        else:
            return {'error': 'Invalid image file type'}
    elif image_url:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], image_url)
        if not os.path.exists(file_path) or not allowed_file(image_url):
            return {'error': 'Image file does not exist in static/image'}
        image_url = f"/static/image/{image_url}"  # store full path in DB

    # Insert into DB
    sql = text("""
        INSERT INTO product (name, price, stock, description, image, category_id, create_at)
        VALUES (:name, :price, :stock, :description, :image, :category_id, :create_at)
    """)
    db.session.execute(sql, {
        "name": name,
        "price": price,
        "stock": stock,
        "description": description,
        "image": image_url,
        "category_id": category_id,
        "create_at": formatted_date,
    })
    db.session.commit()

    return {
        'Message': 'Product created successfully',
        'Products': {
            "name": name,
            "price": price,
            "stock": stock,
            "description": description,
            "image": image_url,
            "category_id": category_id,
            "create_at": display_date,
        }
    }

@app.put('/api/admin/productS/update/<int:id>')
@admin_required
def update_product(id):
    product = Product.query.get(id)
    if not product:
        return jsonify({'error': 'Product not found'})

    data = request.get_json()
    name = data.get('name')
    price = data.get('price')
    stock = data.get('stock')
    description = data.get('description')
    category_id = data.get('category_id')
    image_url = data.get('image')
    if not name:
        return {'error': 'No product name provided'}
    if not price:
        return {'error': 'No price provided'}
    if not stock:
        return {'error': 'No stock provided'}
    if not category_id:
        return {'error': 'No category_id provided'}
    try:
        price = float(price)
        stock = int(stock)
        category_id = int(category_id)
    except ValueError:
        return {'error': 'Invalid numeric value'}
    image_url = product.image
    if 'image_url' in request.files:
        image = request.files['image_url']
        if image and allowed_file(image.filename):
            if product.image:
                old_image_path = product.image.lstrip('/')
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
            filename = f"{uuid.uuid4().hex}_{secure_filename(image.filename)}"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(file_path)
            image_url = f"/static/image/{filename}"
        else:
            return {'error': 'Invalid image file type'}
    product.name = name
    product.price = price
    product.stock = stock
    product.description = description
    product.image = image_url
    product.category_id = category_id
    product.create_at = datetime.now()

    db.session.commit()
    return jsonify({
        'Message': 'Product updated successfully',
        'Product': {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'stock': product.stock,
            'description': product.description,
            'image': product.image,
            'category_id': product.category_id,
            'create_at': product.create_at.strftime("%d-%m-%Y")


        }
    })

@app.delete('/api/admin/products/delete')
@admin_required
def delete_product():
    data = request.get_json()
    product_id = data.get('product_id')

    if not product_id:
        return jsonify({'error': 'Product ID is required'})

    product = Product.query.get(product_id)
    if product is None:
        return jsonify({'error': f'Product with ID {product_id} not found'})

    image_to_delete = product.image
    product_data = {
        'id': product.id,
        'name': product.name,
        'price': product.price,
        'stock': product.stock,
        'description': product.description,
        'image': product.image,
        'category_id': product.category_id,
        'create_at': product.create_at.strftime("%d-%m-%Y") if product.create_at else None
    }
    if image_to_delete:
        image_path = image_to_delete.lstrip('/')
        if os.path.exists(image_path):
            os.remove(image_path)
    db.session.delete(product)
    db.session.commit()
    return jsonify({
        'message': 'Product deleted successfully',
        'Product': product_data
    })


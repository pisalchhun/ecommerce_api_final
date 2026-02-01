from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, create_access_token
from werkzeug.security import check_password_hash, generate_password_hash

from app import app, db
from flask import request, jsonify
from model.user import User
jwt_blocklist = set()

def check_if_token_revoked(jwt_payload):
    jti = jwt_payload["jti"]
    return jti in jwt_blocklist


@app.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    role = "user"
    if not all([name, email, password]):
        return jsonify({"msg": "Name, email, and password are required"}), 400
    if User.query.filter((User.name == name) | (User.email == email)).first():
        return jsonify({"msg": "User with this name or email already exists"}), 400
    hashed_password = generate_password_hash(password)
    user = User(name=name, email=email, password=hashed_password, role=role)
    db.session.add(user)
    db.session.commit()
    return jsonify({"msg": "User registered successfully"}), 201
@app.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("name") or "").strip()
    password = data.get("password") or ""
    user = User.query.filter_by(name=username).first()
    if not user:
        return jsonify({"Message": "Wrong username or password"}), 401
    else:
        if check_password_hash(user.password,password):
            access = create_access_token(
                identity=str(user.id),
                additional_claims={
                    "id": str(user.id),
                    "name": user.name,
                    "email": user.email,
                    "role": user.role

                }
            )
            return jsonify({
                  "message": "You have successfully logged in!",
                  "data": {
                    "access_token": access,
                  }
                })

        else:
            return jsonify({"Message": "Wrong username or password"}), 401

@app.post("/logout")
@jwt_required()
def logout():
    jti = get_jwt()["jti"]
    jwt_blocklist.add(jti)
    return jsonify({"msg": "Successfully logged out"}), 200


@app.get("/me")
@jwt_required()
def me():
    user_id = get_jwt_identity()
    claims = get_jwt()
    return jsonify({
        "id":user_id,
        "name": claims.get("name"),
        "email": claims.get("email"),
        "role": claims.get("role"),
        }
    )

@app.post("/reset-password")
@jwt_required()
def reset_password():
    user_id = get_jwt_identity()
    data = request.get_json(silent=True) or {}

    old_password = data.get("old_password") or ""
    new_password = data.get("new_password") or ""
    confirm_password = data.get("confirm_password") or ""

    if not all([old_password, new_password, confirm_password]):
        return jsonify({"msg": "All password fields are required"}), 400

    if new_password != confirm_password:
        return jsonify({"msg": "New passwords do not match"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not check_password_hash(user.password, old_password):
        return jsonify({"msg": "Old password is incorrect"}), 401

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"msg": "Password reset successfully"}), 200
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['JWT_SECRET_KEY'] = "8f3G7!k2Lp#4vQx9ZrT0wE1sH6yA5bJk"

db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

import model
import route

@app.route('/')
def hello_world():
    return jsonify({
        "status": "ok",
        "message": "API is running"
    })

if __name__ == '__main__':
    app.run(debug=True)

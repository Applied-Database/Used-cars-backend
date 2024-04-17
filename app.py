from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token
import sqlite3
import random
import string

import os
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['JWT_SECRET_KEY'] = 'usedcars500'
jwt = JWTManager(app)
db_path = 'usedCars (2).db'   # Loacl DB Path

def query_db(query, args=(), one=False):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query, args)
    result = cursor.fetchone() if one else cursor.fetchall()
    conn.commit()

    print(result)
    return result

# Login API
@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"message": "Missing JSON in request"}), 400

    email = request.json.get('email', None)
    password = request.json.get('password', None)
    if not email:
        return jsonify({"message": "Missing email"}), 400
    if not password:
        return jsonify({"message": "Missing password "}), 400

    # Check if the user exists!!
    user = query_db("SELECT * FROM Users WHERE email = ? AND password = ?",
                    (email, password), one=True)

    if user:
        access_token = create_access_token(identity=email)
        return jsonify(
            access_token=access_token,
            email=user[0][1],
        )
    else:
        return jsonify({"message": "Invalid username or password"}), 403

# SignUp API
@app.route('/signup', methods=['POST'])
def signup():
    if not request.is_json:
        return jsonify({"message": "Missing JSON in request"}), 400

    email = request.json.get('email', None)
    first_name = request.json.get('first_name', None)
    last_name = request.json.get('last_name', None)
    password = request.json.get('password', None)
    region = request.json.get('city', None)
    user_state=request.json.get('state', None)

    if not email or not first_name or not last_name or not password:
        return jsonify({"message": "Missing parameters"}), 400


    existing_user = query_db("SELECT * FROM Users WHERE email = ?", (email,), one=True)

    if existing_user:
        return jsonify({"message": "User with this emailid already exists"}), 400
    
    region_url="just a default url"
    user_lat=80
    user_long=80
    # Create a new user
    query_db("INSERT INTO Users (email, first_name, last_name, password, region, region_url, user_state,user_lat,user_long) VALUES (?, ?, ?, ?, ?, ?, ?,?,?)",
             (email, first_name, last_name, password, region, region_url, user_state,user_lat,user_long))

    return jsonify({"message": "User registered successfully"}), 201
@app.route('/')

def hello_world():

    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)


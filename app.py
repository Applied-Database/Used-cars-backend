from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token
from flask_jwt_extended import jwt_required  

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
    cursor.close()  
    conn.close() 
    print(result)
    return result

def query_db1(query, args=(), one=False):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(query, args)
    result = cursor.fetchone() if one else cursor.fetchall()
    cursor.close()  
    conn.close()   
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
    user = query_db1("SELECT * FROM Users WHERE email = ? AND password = ?",
                    (email, password), one=True)

    if user:
        access_token = create_access_token(identity=email)
        return jsonify(
            access_token=access_token,
            email=user[0],
            first_name=user[1],
            last_name=user[2],
            region=user[4],
            user_state=user[6]

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


    existing_user = query_db1("SELECT * FROM Users WHERE email = ?", (email,), one=True)

    if existing_user:
        return jsonify({"message": "User with this emailid already exists"}), 400
    
    region_url="just a default url"
    user_lat=80
    user_long=80
    # Create a new user
    query_db("INSERT INTO Users (email, first_name, last_name, password, region, region_url, user_state,user_lat,user_long) VALUES (?, ?, ?, ?, ?, ?, ?,?,?)",
             (email, first_name, last_name, password, region, region_url, user_state,user_lat,user_long))

    return jsonify({"message": "User registered successfully"}), 201

# Displayig all the posting of the vehicles api
@app.route('/vehicle_postings', methods=['GET'])
def get_vehicle_postings():
    vehicle_postings = query_db1("""
        SELECT 
            p.id,
            p.url,
            p.price,
            p.condition,
            p.odometer,
            p.title_status,
            p.VIN,
            p.paint_color,
            p.image_url,
            p.description,
            p.posting_date,
            u.email AS user_email,
            u.first_name,
            u.last_name,
            v.manufacturer,
            v.model AS vehicle_model,
            v.year,
            v.cylinders,
            v.fuel,
            v.transmission,
            v.drive,
            v.size,
            v.type
        FROM Posting p
        INNER JOIN Users u ON p.email = u.email
        INNER JOIN Vehicles v ON p.model = v.model
    """)

  
    postings = [dict(zip(['id', 'url', 'price', 'condition', 'odometer', 
                          'title_status', 'VIN', 'paint_color', 'image_url', 
                          'description', 'posting_date', 'user_email', 
                          'first_name', 'last_name', 'manufacturer', 
                          'vehicle_model', 'year', 'cylinders', 'fuel', 
                          'transmission', 'drive', 'size', 'type'], posting))
                for posting in vehicle_postings]

    return jsonify(postings=postings)

# Update User API
@app.route('/user_profile', methods=['PUT'])
def update_user_profile():
    if not request.is_json:
        return jsonify({"message": "Missing JSON in request"}), 400

    email = request.json.get('email', None)
    new_first_name = request.json.get('first_name', None)
    new_last_name = request.json.get('last_name', None)
    new_password = request.json.get('password', None)  # Remember to hash passwords in production
    new_region = request.json.get('region', None)
    new_user_state = request.json.get('user_state', None)

  
    if not email:
        return jsonify({"message": "Missing email parameter"}), 400


    user = query_db1("SELECT * FROM Users WHERE email = ?", (email,), one=True)
    if not user:
        return jsonify({"message": "User not found"}), 404


    update_data = []
    query_components = []

    if new_first_name:
        query_components.append("first_name = ?")
        update_data.append(new_first_name)
    if new_last_name:
        query_components.append("last_name = ?")
        update_data.append(new_last_name)
    if new_password:
        query_components.append("password = ?")
        update_data.append(new_password) 
    if new_region:
        query_components.append("region = ?")
        update_data.append(new_region)
    if new_user_state:
        query_components.append("user_state = ?")
        update_data.append(new_user_state)
    

    if query_components:
        query = "UPDATE Users SET " + ", ".join(query_components) + " WHERE email = ?"
        update_data.append(email)
        query_db(query, update_data,one=True)
        return jsonify({"message": "User profile updated successfully"}), 200
    else:
        return jsonify({"message": "No fields to update"}), 400

@app.route('/')

def hello_world():

    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)


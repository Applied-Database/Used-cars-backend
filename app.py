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
    new_first_name = request.json.get('firstName', None)
    new_last_name = request.json.get('lastName', None)
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
    
#api to get the vehicle model for dropdown when adding posting 
@app.route('/vehicle_models', methods=['GET'])
def get_vehicle_models():
    
    vehicle_models = query_db1("SELECT model FROM Vehicles")

   
    models_list = [model[0] for model in vehicle_models]

    return jsonify(models_list), 200

#add postings 
@app.route('/add_vehicle_posting', methods=['POST'])
def add_vehicle_posting():
    if not request.is_json:
        return jsonify({"message": "Missing JSON in request"}), 400
    
    # Get data from the request JSON
    email = request.json.get('email', None) 
    url = request.json.get('url', None)
    price = request.json.get('price', None)
    condition = request.json.get('condition', None)
    odometer = request.json.get('odometer', None)
    title_status = request.json.get('title_status', None)
    VIN = request.json.get('VIN', None)
    paint_color = request.json.get('paint_color', None)
    image_url = request.json.get('image_url', None)
    description = request.json.get('description', None)
    posting_date = request.json.get('posting_date', None)
    model = request.json.get('model', None)  


    if not all([url, price, condition, odometer, title_status, VIN, paint_color, image_url, description, posting_date, model]):
        return jsonify({"message": "Missing parameters"}), 400
    

    vehicle_exists = query_db1("SELECT * FROM Vehicles WHERE model = ?", (model,), one=True)
    if not vehicle_exists:
        return jsonify({"message": "Vehicle model not found"}), 404


    query_db("INSERT INTO Posting (url, price, condition, odometer, title_status, VIN, paint_color, image_url, description, posting_date, email, model) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
             (url, price, condition, odometer, title_status, VIN, paint_color, image_url, description, posting_date, email, model))
  
    return jsonify({"message": "Vehicle posting added successfully"}), 201

#get all the user postings
@app.route('/user_postings', methods=['POST'])
def get_user_postings():
    if not request.is_json:
        return jsonify({"message": "Missing JSON in request"}), 400

    current_user_email = request.json.get('email', None)

    if not current_user_email:
        return jsonify({"message": "Missing email parameter"}), 400

    user_postings = query_db1("""
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
        WHERE p.email = ?
    """, (current_user_email,))

    postings = [dict(zip(['id', 'url', 'price', 'condition', 'odometer', 
                          'title_status', 'VIN', 'paint_color', 'image_url', 
                          'description', 'posting_date', 'user_email', 
                          'first_name', 'last_name', 'manufacturer', 
                          'vehicle_model', 'year', 'cylinders', 'fuel', 
                          'transmission', 'drive', 'size', 'type'], posting))
                for posting in user_postings]

    return jsonify(postings=postings), 200

@app.route('/update_vehicle_posting', methods=['PUT'])

def update_vehicle_posting():
    if not request.is_json:
        return jsonify({"message": "Missing JSON in request"}), 400
    
    posting_id=request.json.get('id')
    url = request.json.get('url')
    price = request.json.get('price')
    condition = request.json.get('condition')
    odometer = request.json.get('odometer')
    title_status = request.json.get('title_status')
    VIN = request.json.get('VIN')
    paint_color = request.json.get('paint_color')
    image_url = request.json.get('image_url')
    description = request.json.get('description')
    posting_date = request.json.get('posting_date')
    model = request.json.get('model')  

    posting = query_db1("SELECT * FROM Posting WHERE id = ?", (posting_id,), one=True)
    if not posting:
        return jsonify({"message": "Posting not found or you do not have permission to update this posting"}), 404
    
    vehicle_exists = query_db1("SELECT * FROM Vehicles WHERE model = ?", (model,), one=True)
    if not vehicle_exists:
        return jsonify({"message": "Vehicle model not found"}), 404


    
    update_data = []
    query_components = []

    if url is not None:
        query_components.append("url = ?")
        update_data.append(url)
    if price is not None:
        query_components.append("price = ?")
        update_data.append(price)
    if condition is not None:
        query_components.append("condition = ?")
        update_data.append(condition)
    if odometer is not None:
        query_components.append("odometer = ?")
        update_data.append(odometer)
    if title_status is not None:
        query_components.append("title_status = ?")
        update_data.append(title_status)
    if VIN is not None:
        query_components.append("VIN = ?")
        update_data.append(VIN)
    if paint_color is not None:
        query_components.append("paint_color = ?")
        update_data.append(paint_color)
    if image_url is not None:
        query_components.append("image_url = ?")
        update_data.append(image_url)
    if description is not None:
        query_components.append("description = ?")
        update_data.append(description)
    if posting_date is not None:
        query_components.append("posting_date = ?")
        update_data.append(posting_date)
    if model is not None:
        query_components.append("model = ?")
        update_data.append(model)
    

    if query_components:
        update_query = "UPDATE Posting SET " + ", ".join(query_components) + " WHERE id = ?"
        update_data.append(posting_id)
        query_db(update_query, update_data)
        return jsonify({"message": "Vehicle posting updated successfully"}), 200
    else:
        return jsonify({"message": "No update data provided"}), 400
    
#deleting the posting 
@app.route('/delete_vehicle_posting', methods=['POST'])

def delete_vehicle_posting():
    posting_id=request.json.get('id',None)

    posting = query_db1("SELECT * FROM Posting WHERE id = ?", (posting_id,), one=True)
    if not posting:
        return jsonify({"message": "Posting not found or you do not have permission to delete this posting"}), 404


    query_db("DELETE FROM Posting WHERE id = ?", (posting_id,))
  
    return jsonify({"message": "Vehicle posting deleted successfully"}), 200



@app.route('/')

def hello_world():

    return 'Hello, World!'

if __name__ == '__main__':
    app.run(debug=True)


from flask import Flask, request, jsonify, render_template,redirect, url_for
import requests
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
import os
from db import users



app = Flask(__name__)
CORS(app)
bcrypt = Bcrypt(app)

load_dotenv()
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
jwt = JWTManager(app)

N2YO_API_KEY = "RZSQL9-CCVNNJ-VFTQ6K-5FIU"  # Your API key

@app.route('/')
def home():
    return render_template('o.html')

@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/signup')
def signup_page():
    return render_template('signup.html')


@app.route('/logout')
def logout():
    # Clear the token from localStorage on the client side
    return redirect(url_for('login_page'))

    # 🔥 Signup API
# ✅ Signup Route - Store data in MongoDB
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Check for duplicate username
    if users.find_one({"username": username}):
        return jsonify({"error": "Username already exists"}), 409

    # Store hashed password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    users.insert_one({
        "username": username,
        "password": hashed_password
    })

    print(f"✅ User {username} added successfully.")
    
    return jsonify({"message": "User registered successfully"}), 201


# 🔑 Login Route - Authenticate and generate JWT
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = users.find_one({"username": username})

    if not user or not bcrypt.check_password_hash(user['password'], password):
        return jsonify({"error": "Invalid username or password"}), 401

    # Generate JWT token
    token = create_access_token(identity=str(user['_id']))

    return jsonify({"token": token, "message": "Login successful"}), 200

@app.route('/satellite/search', methods=['GET'])
def search_satellite():
    sat_id = request.args.get('id', '').strip()  # Get satellite NORAD ID

    if not sat_id:
        return jsonify({"error": "Satellite ID is required"}), 400

    url = f"https://api.n2yo.com/rest/v1/satellite/positions/{sat_id}/0/0/0/1/?apiKey={N2YO_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch satellite data"}), response.status_code

    data = response.json()

    if "positions" not in data or not data["positions"]:
        return jsonify({"error": "No position data available"}), 404

    position = data["positions"][0]

    return jsonify({
        "name": data["info"]["satname"],
        "latitude": position["satlatitude"],
        "longitude": position["satlongitude"],
        "altitude": position["sataltitude"]
    })



if __name__ == "__main__":
    app.run(debug=True)

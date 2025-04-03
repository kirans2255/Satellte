from flask import Flask, request, jsonify, render_template
import requests
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, JWTManager

app = Flask(__name__)
CORS(app)  # Apply CORS early

# 🔹 Configure PostgreSQL Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/satellite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'supersecretkey'  # Change this in production

# 🔹 Initialize Extensions
db = SQLAlchemy()
db.init_app(app)  # ✅ Properly initialize with app
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# 🔹 Define User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# 🔹 Create tables inside an application context
with app.app_context():
    db.create_all()  # ✅ Creates the users table in your PostgreSQL database

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

# 🔹 SIGNUP ROUTE
@app.route('/signup-page', methods=['POST'])
def signup():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    # Check if user exists
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'User already exists'}), 409

    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    
    # Save user
    new_user = User(username=username, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201

# 🔹 LOGIN ROUTE
@app.route('/login-page', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    
    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Generate JWT token
    access_token = create_access_token(identity=user.id)
    return jsonify({'message': 'Login successful', 'token': access_token}), 200

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

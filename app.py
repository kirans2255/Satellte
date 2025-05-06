from flask import Flask, request, jsonify, render_template
import requests
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, JWTManager
from datetime import datetime, timedelta
import math

app = Flask(__name__)
CORS(app)  # Apply CORS early

# 🔹 Configure PostgreSQL Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1234@localhost/Satellite'
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
    email = db.Column(db.String(120), unique=True, nullable=False)  # 🔹 Add this line
    password = db.Column(db.String(200), nullable=False)

# 🔹 Define SatelliteSearch Model (to store search history)
class SatelliteSearch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Link to User
    username = db.Column(db.String(100), nullable=False)  # Username of the user who made the search
    norad_id = db.Column(db.String(100), nullable=False)  # NORAD ID searched
    date = db.Column(db.DateTime, default=datetime.utcnow)  # Date when the search was made

    # Relationship with User
    user = db.relationship('User', backref=db.backref('satellite_searches', lazy=True))

    def __repr__(self):
        return f"<SatelliteSearch(username={self.username}, norad_id={self.norad_id}, date={self.date})>"

# 🔹 Create tables inside an application context
with app.app_context():
    db.create_all()  # ✅ Creates the users table and satellite_search table

N2YO_API_KEY = "RZSQL9-CCVNNJ-VFTQ6K-5FIU"  # Your API key

# Sample satellite data (in production, this would come from a database)
SATELLITES = [
    {"id": "25544", "name": "ISS (ZARYA)", "type": "space station"},
    {"id": "20580", "name": "HST (Hubble)", "type": "space telescope"},
    {"id": "37849", "name": "GPS BIIF-1", "type": "navigation"},
    {"id": "39084", "name": "TDRS 11", "type": "communications"},
    {"id": "33591", "name": "NOAA 19", "type": "weather"},
    {"id": "43013", "name": "STARLINK-1", "type": "communications"},
    {"id": "48274", "name": "STARLINK-1789", "type": "communications"},
    {"id": "40940", "name": "TIANGONG 2", "type": "space station"},
    {"id": "40957", "name": "WORLDVIEW-4", "type": "earth observation"},
    {"id": "29155", "name": "GOES 13", "type": "weather"},
    {"id": "25338", "name": "NAVSTAR GPS IIR-2", "type": "navigation"},
    {"id": "27424", "name": "SWIFT", "type": "space telescope"},
    {"id": "36516", "name": "WISE", "type": "space telescope"},
    {"id": "27386", "name": "XMM-NEWTON", "type": "space telescope"},
    {"id": "26871", "name": "USA 164 (GPS)", "type": "navigation"}
]

@app.route('/')
def home():
    return render_template('o.html')

@app.route('/telementary')
def telemetry_page():
    return render_template('telementary.html')

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
    email = data.get('email')  # 🔹 Get email from request
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400

    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'Username already exists'}), 409

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email already in use'}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password=hashed_password)
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
    username = request.args.get('username', '').strip()  # Get username from query parameters

    if not sat_id:
        return jsonify({"error": "Satellite ID is required"}), 400

    # Call the external API
    url = f"https://api.n2yo.com/rest/v1/satellite/positions/{sat_id}/0/0/0/1/?apiKey={N2YO_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch satellite data"}), response.status_code

    data = response.json()

    if "positions" not in data or not data["positions"]:
        return jsonify({"error": "No position data available"}), 404

    position = data["positions"][0]

    # Store search history without JWT; store user info via username
    if username:
        user = User.query.filter_by(username=username).first()  # Find user by username
        if user:
            # Create and store the satellite search data in the database
            new_search = SatelliteSearch(user_id=user.id, username=username, norad_id=sat_id)
            db.session.add(new_search)
            db.session.commit()  # Commit the transaction to save the search

            print(f"Search stored for {username} with NORAD ID {sat_id}.")  # Debugging line

    return jsonify({
        "name": data["info"]["satname"],
        "latitude": position["satlatitude"],
        "longitude": position["satlongitude"],
        "altitude": position["sataltitude"]
    })

@app.route('/api/satellites')
def get_satellites():
    return jsonify(SATELLITES)

@app.route('/api/satellite/<sat_id>/orbit', methods=['GET'])
def get_satellite_orbit(sat_id):
    try:
        # Validate satellite ID
        if not sat_id or not sat_id.isdigit():
            return jsonify({"error": "Invalid satellite ID"}), 400

        # Get TLE data for orbit prediction
        tle_url = f"https://api.n2yo.com/rest/v1/satellite/tle/{sat_id}/&apiKey={N2YO_API_KEY}"
        tle_response = requests.get(tle_url)
        
        if tle_response.status_code != 200:
            return jsonify({"error": "Failed to fetch TLE data"}), tle_response.status_code
            
        tle_data = tle_response.json()

        if "tle" not in tle_data:
            return jsonify({"error": "No TLE data available"}), 404

        # Get current position for reference
        pos_url = f"https://api.n2yo.com/rest/v1/satellite/positions/{sat_id}/0/0/0/1/?apiKey={N2YO_API_KEY}"
        pos_response = requests.get(pos_url)
        
        if pos_response.status_code != 200:
            return jsonify({"error": "Failed to fetch position data"}), pos_response.status_code
            
        pos_data = pos_response.json()

        if "positions" not in pos_data or not pos_data["positions"]:
            return jsonify({"error": "No position data available"}), 404

        # Calculate orbit path points (more accurate)
        orbit_points = []
        current_time = datetime.utcnow()
        
        try:
            # Calculate points for one full orbit (approximately 90 minutes for LEO)
            for i in range(-45, 45, 5):  # 5-minute intervals, 45 minutes before and after
                future_time = current_time + timedelta(minutes=i)
                # This is a simplified calculation. In production, you'd use proper orbital mechanics
                # or a library like skyfield for more accurate predictions
                lat = float(pos_data["positions"][0]["satlatitude"]) + math.sin(math.radians(i * 4)) * 5
                lon = float(pos_data["positions"][0]["satlongitude"]) + math.cos(math.radians(i * 4)) * 5
                alt = float(pos_data["positions"][0]["sataltitude"])
                
                orbit_points.append({
                    "latitude": lat,
                    "longitude": lon,
                    "altitude": alt,
                    "timestamp": future_time.isoformat()
                })
        except (ValueError, KeyError) as e:
            return jsonify({"error": f"Error calculating orbit points: {str(e)}"}), 500

        if not orbit_points:
            return jsonify({"error": "No orbit points calculated"}), 404

        return jsonify(orbit_points)
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/satellite/<sat_id>/position', methods=['GET'])
def get_satellite_position(sat_id):
    try:
        # Validate satellite ID
        if not sat_id or not sat_id.isdigit():
            return jsonify({"error": "Invalid satellite ID"}), 400

        # Get current position
        url = f"https://api.n2yo.com/rest/v1/satellite/positions/{sat_id}/0/0/0/1/?apiKey={N2YO_API_KEY}"
        response = requests.get(url)
        
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch position data"}), response.status_code
            
        data = response.json()

        if "positions" not in data or not data["positions"]:
            return jsonify({"error": "No position data available"}), 404

        position = data["positions"][0]
        
        # Get additional satellite info
        info_url = f"https://api.n2yo.com/rest/v1/satellite/visualpasses/{sat_id}/0/0/0/1/300/&apiKey={N2YO_API_KEY}"
        info_response = requests.get(info_url)
        
        if info_response.status_code != 200:
            return jsonify({"error": "Failed to fetch satellite info"}), info_response.status_code
            
        info_data = info_response.json()

        # Calculate velocity and period
        velocity = 7.66  # Default to ISS velocity
        period = 90  # Default to ISS period
        if "info" in info_data and "satalt" in info_data["info"]:
            # Rough velocity calculation based on altitude
            altitude = float(info_data["info"]["satalt"])
            velocity = math.sqrt(398600.4418 / (6371 + altitude))  # Simplified orbital velocity formula
            period = 2 * math.pi * math.sqrt((6371 + altitude)**3 / 398600.4418) / 60  # Convert to minutes

        # Get next pass time
        next_pass = None
        if "passes" in info_data and info_data["passes"]:
            next_pass_time = datetime.fromtimestamp(info_data["passes"][0]["startUTC"])
            next_pass = next_pass_time.strftime("%H:%M:%S UTC")

        # Get satellite type
        sat_type = "Unknown"
        for sat in SATELLITES:
            if sat["id"] == sat_id:
                sat_type = sat["type"]
                break

        return jsonify({
            "name": data["info"]["satname"],
            "type": sat_type,
            "latitude": float(position["satlatitude"]),
            "longitude": float(position["satlongitude"]),
            "altitude": float(position["sataltitude"]),
            "velocity": velocity,
            "period": period,
            "next_pass": next_pass
        })
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"API request failed: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/logout', methods=['POST'])
def logout():
    # No server-side session to clear, but return success
    return jsonify({'message': 'Logged out successfully'}), 200

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

if __name__ == "__main__":
    app.run(debug=True)

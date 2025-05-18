from flask import Flask, request, jsonify, render_template , session, redirect, url_for
import requests
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import create_access_token, JWTManager
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from sgp4.api import Satrec
from skyfield.api import EarthSatellite, load
import os
from numpy import linalg as LA
import math
from datetime import datetime
import json
from sqlalchemy import func


app = Flask(__name__)
CORS(app)  # Apply CORS early
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  #
    is_blocked = db.Column(db.Boolean, default=False)  # New field


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


class SatelliteData(db.Model):
    __tablename__ = 'satellite_data'   # must match your DB table name

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    name = db.Column(db.String(200))
    type = db.Column(db.String(200))
    altitude = db.Column(db.Float)
    velocity = db.Column(db.Float)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    period = db.Column(db.Float)
    next_pass = db.Column(db.String(200))
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

# Satellite model
class Satellite(db.Model):
    id = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    altitude = db.Column(db.Float)
    velocity = db.Column(db.Float)
    period = db.Column(db.Float)
    next_pass = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'velocity': self.velocity,
            'period': self.period,
            'next_pass': self.next_pass.isoformat() if self.next_pass else None
        }

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

def initialize_default_satellites():
    """Initialize the database with default satellites if they don't exist."""
    with app.app_context():
        for sat_data in SATELLITES:
            # Check if satellite already exists
            existing_satellite = Satellite.query.get(sat_data['id'])
            if not existing_satellite:
                # Create new satellite with default values
                satellite = Satellite(
                    id=sat_data['id'],
                    name=sat_data['name'],
                    type=sat_data['type'],
                    latitude=0.0,  # Default values
                    longitude=0.0,
                    altitude=0.0,
                    velocity=0.0,
                    period=0.0,
                    next_pass=None
                )
                db.session.add(satellite)
        
        try:
            db.session.commit()
            print("Default satellites initialized successfully")
        except Exception as e:
            db.session.rollback()
            print(f"Error initializing default satellites: {str(e)}")

# Initialize default satellites when the app starts
initialize_default_satellites()

@app.route('/')
def home():
    return render_template('o.html')

@app.route('/telemetry')
def telemetry_page():
    return render_template('telemetry.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')
# Admin login page route
@app.route('/admin')
def admin_login_page():
    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')



# 🔹 SIGNUP ROUTE
@app.route('/signup-user', methods=['POST'])
def signup_user():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400

    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({'error': 'Username or email already in use'}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_user = User(username=username, email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully'}), 201


@app.route('/signup-admin', methods=['POST'])
def signup_admin():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not username or not email or not password:
        return jsonify({'error': 'Username, email, and password are required'}), 400

    if Admin.query.first():
        return jsonify({'error': 'Only one admin allowed'}), 403

    if Admin.query.filter_by(username=username).first() or Admin.query.filter_by(email=email).first():
        return jsonify({'error': 'Username or email already in use'}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    new_admin = Admin(username=username, email=email, password=hashed_password)
    db.session.add(new_admin)
    db.session.commit()

    return jsonify({'message': 'Admin created successfully'}), 201



# 🔹 LOGIN ROUTE
@app.route('/login-user', methods=['POST'])
def login_user():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if not user or not bcrypt.check_password_hash(user.password, password):
        return jsonify({'error': 'Invalid user credentials'}), 401

    if user.is_blocked:
        return jsonify({'error': 'Your account is blocked. Contact admin.'}), 403

    access_token = create_access_token(identity=user.id, additional_claims={"role": "user"})
    return jsonify({'message': 'User login successful', 'token': access_token}), 200



@app.route('/login-admin', methods=['POST'])
def login_admin():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    admin = Admin.query.filter_by(username=username).first()
    if not admin or not bcrypt.check_password_hash(admin.password, password):
        return jsonify({'error': 'Invalid admin credentials'}), 401

    access_token = create_access_token(identity=admin.id, additional_claims={"role": "admin"})
    return jsonify({'message': 'Admin login successful', 'token': access_token}), 200



@app.route('/satellite/search', methods=['GET'])
def search_satellite():
    sat_id = request.args.get('id', '').strip()
    username = request.args.get('username', '').strip()

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

    # Store search history and log interaction
    if username:
        user = User.query.filter_by(username=username).first()
        if user:
            # Create and store the satellite search data
            new_search = SatelliteSearch(user_id=user.id, username=username, norad_id=sat_id)
            db.session.add(new_search)
            
            # Log the search interaction
            interaction = UserSatelliteInteraction(
                user_id=user.id,
                username=username,
                satellite_id=sat_id,
                interaction_type='search'
            )
            db.session.add(interaction)
            db.session.commit()

    return jsonify({
        "name": data["info"]["satname"],
        "latitude": position["satlatitude"],
        "longitude": position["satlongitude"],
        "altitude": position["sataltitude"]
    })

@app.route('/api/satellite/store', methods=['POST'])
def store_satellite():
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'id' not in data or 'name' not in data:
            return jsonify({'error': 'Missing required fields'}), 400

        # Get username from request headers or query params
        username = request.headers.get('X-Username') or request.args.get('username')
        
        # Check if satellite already exists
        existing_satellite = Satellite.query.get(data['id'])
        if existing_satellite:
            # Log interaction if user is logged in
            if username:
                user = User.query.filter_by(username=username).first()
                if user:
                    interaction = UserSatelliteInteraction(
                        user_id=user.id,
                        username=username,
                        satellite_id=data['id'],
                        interaction_type='add'
                    )
                    db.session.add(interaction)
                    db.session.commit()
            return jsonify({'code': 'DUPLICATE', 'message': 'Satellite already exists'}), 200

        # Create new satellite
        satellite = Satellite(
            id=data['id'],
            name=data['name'],
            type=data.get('type'),
            latitude=data.get('latitude'),
            longitude=data.get('longitude'),
            altitude=data.get('altitude'),
            velocity=data.get('velocity'),
            period=data.get('period'),
            next_pass=datetime.fromisoformat(data['next_pass']) if data.get('next_pass') else None
        )

        db.session.add(satellite)
        
        # Log interaction if user is logged in
        if username:
            user = User.query.filter_by(username=username).first()
            if user:
                interaction = UserSatelliteInteraction(
                    user_id=user.id,
                    username=username,
                    satellite_id=data['id'],
                    interaction_type='add'
                )
                db.session.add(interaction)
        
        db.session.commit()
        return jsonify(satellite.to_dict()), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# New route to log satellite click
@app.route('/api/satellite/<sat_id>/click', methods=['POST'])
def log_satellite_click(sat_id):
    try:
        username = request.headers.get('X-Username') or request.args.get('username')
        if not username:
            return jsonify({'error': 'Username required'}), 400

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Log the click interaction
        interaction = UserSatelliteInteraction(
            user_id=user.id,
            username=username,
            satellite_id=sat_id,
            interaction_type='click'
        )
        db.session.add(interaction)
        db.session.commit()

        return jsonify({'message': 'Click logged successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# New route to get user's satellite interactions
@app.route('/api/user/<username>/interactions', methods=['GET'])
def get_user_interactions(username):
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        interactions = UserSatelliteInteraction.query.filter_by(user_id=user.id).all()
        return jsonify([{
            'satellite_id': interaction.satellite_id,
            'interaction_type': interaction.interaction_type,
            'interaction_date': interaction.interaction_date.isoformat(),
            'satellite_name': interaction.satellite.name if interaction.satellite else None
        } for interaction in interactions]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Update the existing satellites route to include stored satellites
@app.route('/api/satellites')
def get_satellites():
    try:
        # Get all stored satellites
        stored_satellites = Satellite.query.all()
        return jsonify([sat.to_dict() for sat in stored_satellites])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    filename = secure_filename(file.filename)

    if not filename.endswith(('.txt', '.json')):
        return jsonify({'error': 'Invalid file format. Only .txt or .json allowed.'})

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        tle_lines = [line.strip() for line in lines if line.strip()]
        if len(tle_lines) < 3:
            return jsonify({'error': 'Invalid TLE format'})

        name, tle1, tle2 = tle_lines[0], tle_lines[1], tle_lines[2]

        # Use Skyfield to process TLE
        ts = load.timescale()
        satellite = EarthSatellite(tle1, tle2, name, ts)
        t = ts.now()
        geocentric = satellite.at(t)

        # Get position and velocity
        subpoint = geocentric.subpoint()
        altitude = subpoint.elevation.km
        latitude = subpoint.latitude.degrees
        longitude = subpoint.longitude.degrees

        # ✅ Correct velocity calculation
        velocity_vector = geocentric.velocity.km_per_s
        speed = LA.norm(velocity_vector)

        return jsonify({
            'name': name,
            'type': 'CSS (TIANHE)',  # Or detect type from TLE source
            'altitude': round(altitude, 2),
            'velocity': round(speed, 2),
            'latitude': round(latitude, 2),
            'longitude': round(longitude, 2)
        })

    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'})


@app.route('/upload', methods=['POST'])
def upload():
    username = request.form.get('username')
    if not username:
        return jsonify({"error": "username is required"}), 400

    file = request.files.get('file')
    if not file:
        return jsonify({"error": "file is required"}), 400

    try:
        content = file.read().decode('utf-8')
        data = json.loads(content)

        satellite = SatelliteData(
            username=username,
            name=data.get('name'),
            type=data.get('type'),
            altitude=float(data.get('altitude', 0)),
            velocity=float(data.get('velocity', 0)),
            latitude=float(data.get('latitude', 0)),
            longitude=float(data.get('longitude', 0)),
            period=float(data.get('period', 0)) if data.get('period') else None,
            next_pass=data.get('nextPass')
        )

        db.session.add(satellite)
        db.session.commit()

        return jsonify(data)

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route('/api/user-signups-weekly')
def weekly_signups():
    today = datetime.utcnow()
    start_date = today - timedelta(days=6)  # Last 7 days

    # Group by day and count users
    results = (
        db.session.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        )
        .filter(User.created_at >= start_date)
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )

    data = [{'date': result.date.strftime('%Y-%m-%d'), 'count': result.count} for result in results]
    return jsonify(data)

@app.route('/users/<int:user_id>/block', methods=['POST'])
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blocked = True
    db.session.commit()
    return jsonify({"message": f"User {user.username} blocked"}), 200

@app.route('/users/<int:user_id>/unblock', methods=['POST'])
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.is_blocked = False
    db.session.commit()
    return jsonify({"message": f"User {user.username} unblocked"}), 200


@app.route('/users')
def show_list():
    users = User.query.all()
    print("Fetched users:", users)
    return render_template('users.html', users=users)


@app.route('/users')
def users_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('users.html', users=users)

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

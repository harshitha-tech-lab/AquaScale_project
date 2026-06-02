import os
import cv2
import json
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, History, init_db
from model_loader import load_classification_model, classify_fish
from length_estimator import detect_and_crop, calculate_segmentation_metrics, get_models
from data_manager import estimate_weight, get_growth_phase

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change this to a random secret key
UPLOAD_FOLDER = 'static/uploads'
DATASET_FOLDER = 'Dataset'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATASET_FOLDER, exist_ok=True)

# Initialize Database
init_db()

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Initialize Models at Startup (Global Cache)
classification_model = load_classification_model()
yolo_model, fastsam_model = get_models() # This initializes them in length_estimator

@app.route('/')
@login_required
def index():
    user_history = User.get_user_history(current_user.id)
    return render_template('index.html', history=user_history)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.find_by_username(username)
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.find_by_username(username):
            flash('Username already exists')
        else:
            hashed_password = generate_password_hash(password)
            User.create(username, hashed_password)
            flash('Registration successful. Please login.')
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    # Step 1: Detect & Classify ONLY
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    # 1. Detect & Crop Fish (Uses Global YOLO)
    fish_crop = detect_and_crop(filepath)

    if fish_crop is None:
        return jsonify({'error': 'Could not detect any fish in the image.'}), 400

    # 2. Classify (Uses Global Classifier)
    species = classify_fish(classification_model, filepath)

    return jsonify({
        'species': species,
        'image_url': f'/{filepath}',
        'filename': file.filename 
    })

@app.route('/calculate_length', methods=['POST'])
@login_required
def calculate_length():
    # Step 2: Segmentation & Length
    data = request.json
    if not data or 'filename' not in data or 'species' not in data:
        return jsonify({'error': 'Missing data'}), 400
    
    filename = data['filename']
    species = data['species']
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    # 3. Calculate Segmentation Metrics (Uses Global Models)
    fish_px, ref_px, processed_path = calculate_segmentation_metrics(filepath)

    if ref_px == 0:
        return jsonify({'error': 'Could not detect Reference object (Orange Card).'}), 400

    # 4. Calculate Real Length
    known_ref_cm = 9.0 if species == 'Tilapia' else 30.0
    
    pixels_per_cm = ref_px / known_ref_cm
    fish_length_cm = fish_px / pixels_per_cm

    # 5. Weight Estimation
    weight = estimate_weight(fish_length_cm, species)

    # 6. Growth Phase Estimation
    growth_phase = get_growth_phase(species, fish_length_cm)

    # Save to History
    History.save_prediction(
        user_id=current_user.id,
        image_path=f'{os.path.join(UPLOAD_FOLDER, processed_path)}',
        species=species,
        length=fish_length_cm,
        weight=weight
    )

    return jsonify({
        'length': fish_length_cm,
        'weight': weight,
        'growth_phase': growth_phase,
        'processed_image_url': f'/{os.path.join(UPLOAD_FOLDER, processed_path)}'
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)

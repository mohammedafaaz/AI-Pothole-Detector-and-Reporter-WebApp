from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import cv2
import os
import math
import uuid
import smtplib
import ssl
import requests
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from ultralytics import YOLO
from PIL import Image as PILImage
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import traceback
import sys
import json
from functools import wraps
import google.generativeai as genai
import base64
import io
import time
from collections import defaultdict
import logging

# Note: Database imports removed - using localStorage only

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Simple rate limiting
request_counts = defaultdict(list)
RATE_LIMIT_REQUESTS = 100  # requests per window
RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds

# Initialize Flask app
app = Flask(__name__, static_url_path='/static')

# Enable CORS for React frontend
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000', 'http://localhost:5173'])

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# API Configuration
API_VERSION = "v1"
API_PREFIX = f"/api/{API_VERSION}"

# Load environment variables
load_dotenv()

# Configuration with fallbacks
config = {
    'MODEL_PATH': os.getenv('MODEL_PATH', 'best.pt'),
    'EMAIL_USER': os.getenv('EMAIL_USER'),
    'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD'),
    'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'SMTP_PORT': int(os.getenv('SMTP_PORT', 587)),
    'CONFIDENCE_THRESHOLD': float(os.getenv('CONFIDENCE_THRESHOLD', 0.25)),
    'IMAGE_SIZE': int(os.getenv('IMAGE_SIZE', 640)),
    'MAPBOX_ACCESS_TOKEN': os.getenv('MAPBOX_ACCESS_TOKEN', ''),
    'API_KEY': os.getenv('API_KEY', None),  # Optional API key for authentication
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', '')  # Gemini API key
}

# Initialize Gemini AI
gemini_enabled = False
gemini_model = None
gemini_fallback_model = None

if config['GEMINI_API_KEY']:
    try:
        genai.configure(api_key=config['GEMINI_API_KEY'])
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        # Initialize fallback model
        try:
            gemini_fallback_model = genai.GenerativeModel('gemini-1.0-pro-vision-latest')
            print("✅ Gemini AI initialized with fallback model")
        except Exception as e:
            print(f"⚠️ Fallback model not available: {e}")

        gemini_enabled = True
        print("✅ Gemini AI initialized successfully")
    except Exception as e:
        print(f"❌ Gemini AI initialization failed: {e}")
        gemini_enabled = False
else:
    print("⚠️ Gemini API key not provided - AI descriptions disabled")

# Print configuration for debugging
print("\nConfiguration values:")
for key, value in config.items():
    if key in ['EMAIL_PASSWORD', 'MAPBOX_ACCESS_TOKEN', 'GEMINI_API_KEY'] and value:
        print(f"{key}: {'*' * len(value)}")
    else:
        print(f"{key}: {value}")
print(f"Gemini AI enabled: {gemini_enabled}")

# Validate configuration
def validate_config():
    """Validate required configuration values"""
    errors = []

    # Check required values
    if not config['MODEL_PATH']:
        errors.append("MODEL_PATH is required")
    elif not os.path.exists(config['MODEL_PATH']):
        errors.append(f"Model file not found: {config['MODEL_PATH']}")

    # Validate numeric values
    try:
        if config['CONFIDENCE_THRESHOLD'] < 0 or config['CONFIDENCE_THRESHOLD'] > 1:
            errors.append("CONFIDENCE_THRESHOLD must be between 0 and 1")
    except (ValueError, TypeError):
        errors.append("CONFIDENCE_THRESHOLD must be a valid number")

    try:
        if config['IMAGE_SIZE'] <= 0:
            errors.append("IMAGE_SIZE must be a positive integer")
    except (ValueError, TypeError):
        errors.append("IMAGE_SIZE must be a valid integer")

    if errors:
        logger.error(f"Configuration validation failed:")
        for error in errors:
            logger.error(f"  - {error}")
        sys.exit(1)

    logger.info("Configuration validation passed")

validate_config()

# Check for email configuration
email_enabled = bool(config['EMAIL_USER'] and config['EMAIL_PASSWORD'])
if not email_enabled:
    print("\nWARNING: Email configuration not found. Email notifications will be disabled.")
    print("To enable email notifications, set EMAIL_USER and EMAIL_PASSWORD in your .env file")

# Extract configuration
MODEL_PATH = config['MODEL_PATH']
EMAIL_USER = config['EMAIL_USER']
EMAIL_PASSWORD = config['EMAIL_PASSWORD'].replace(' ', '') if config['EMAIL_PASSWORD'] else None
SMTP_SERVER = config['SMTP_SERVER']
SMTP_PORT = config['SMTP_PORT']
CONFIDENCE_THRESHOLD = config['CONFIDENCE_THRESHOLD']
IMAGE_SIZE = config['IMAGE_SIZE']
MAPBOX_ACCESS_TOKEN = config['MAPBOX_ACCESS_TOKEN']

# Folder setup
UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load YOLO model
try:
    print(f"\nLoading model from: {MODEL_PATH}")
    model = YOLO(MODEL_PATH)
    print("Model loaded successfully")
    print(f"Model classes: {list(model.names.values())}")
except Exception as e:
    print(f"Error loading model: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

# Rate limiting function
def check_rate_limit(client_ip):
    """Check if client has exceeded rate limit"""
    current_time = time.time()

    # Clean old requests outside the window
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]

    # Check if limit exceeded
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False

    # Add current request
    request_counts[client_ip].append(current_time)
    return True

# API Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check rate limit
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        if not check_rate_limit(client_ip):
            return jsonify({
                'success': False,
                'error': 'Rate limit exceeded. Please try again later.',
                'code': 'RATE_LIMIT_EXCEEDED'
            }), 429

        if config['API_KEY']:
            api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
            if not api_key or api_key != config['API_KEY']:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or missing API key',
                    'code': 'UNAUTHORIZED'
                }), 401
        return f(*args, **kwargs)
    return decorated_function

# Helper function to standardize API responses
def create_api_response(success=True, data=None, error=None, code=None, message=None):
    response = {
        'success': success,
        'timestamp': datetime.now().isoformat(),
        'version': API_VERSION
    }

    if success:
        response['data'] = data or {}
        if message:
            response['message'] = message
    else:
        response['error'] = error or 'Unknown error'
        response['code'] = code or 'INTERNAL_ERROR'

    return response

# Helper function to process detection results
def process_detection_results(results, image_width, image_height, input_path):
    detections = []
    image_diag = math.sqrt(image_width**2 + image_height**2)

    for r in results:
        for box in r.boxes:
            cls = model.names[int(box.cls)]
            conf = float(box.conf)

            # Calculate dimensions and coordinates
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            width, height = x2 - x1, y2 - y1
            box_diag = math.sqrt(width**2 + height**2)
            relative_diag = box_diag / image_diag

            # Determine severity based on relative size
            if relative_diag < 0.20:
                severity = 'Low'
            elif relative_diag < 0.50:
                severity = 'Medium'
            else:
                severity = 'High'

            detection = {
                'class': cls,
                'confidence': round(conf, 3),
                'severity': severity,
                'bbox': {
                    'x1': round(x1, 2),
                    'y1': round(y1, 2),
                    'x2': round(x2, 2),
                    'y2': round(y2, 2),
                    'width': round(width, 2),
                    'height': round(height, 2)
                },
                'relative_size': round(relative_diag, 3)
            }
            detections.append(detection)

    return detections

def generate_static_map(latitude, longitude, severity):
    """Generate a static map image using Mapbox"""
    print(f"generate_static_map called with: lat={latitude}, lng={longitude}, severity={severity}")
    if not MAPBOX_ACCESS_TOKEN:
        print("Mapbox access token not configured")
        return None

    try:
        # Determine marker color based on severity
        if severity == 'High':
            color = 'ff0000'  # Red
            size = 'l'
        elif severity == 'Medium':
            color = 'ffaa00'  # Orange
            size = 'm'
        else:
            color = '00ff00'  # Green
            size = 's'

        # Create URL for static map
        base_url = "https://api.mapbox.com/styles/v1/mapbox/streets-v12/static"
        marker = f"pin-{size}+{color}({longitude},{latitude})"
        zoom = 14
        size = "600x400"

        map_url = f"{base_url}/{marker}/{longitude},{latitude},{zoom}/{size}?access_token={MAPBOX_ACCESS_TOKEN}"

        # Download map image
        print(f"Requesting map from URL: {map_url}")
        response = requests.get(map_url)
        print(f"Mapbox API response: {response.status_code}")

        if response.status_code == 200:
            map_filename = f"map_{uuid.uuid4().hex}.png"
            map_path = os.path.join(OUTPUT_FOLDER, map_filename)
            print(f"Saving map to: {map_path}")

            with open(map_path, 'wb') as f:
                f.write(response.content)

            print(f"Map saved successfully: {os.path.exists(map_path)}")
            return map_path
        else:
            print(f"Mapbox API error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Error generating static map: {str(e)}")
        traceback.print_exc()
        return None

def get_address_from_coordinates(latitude, longitude):
    """Get detailed address from coordinates using Mapbox Geocoding API"""
    if not MAPBOX_ACCESS_TOKEN:
        return None

    try:
        # Mapbox Geocoding API for reverse geocoding
        geocoding_url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{longitude},{latitude}.json?access_token={MAPBOX_ACCESS_TOKEN}"

        print(f"Getting address from: {geocoding_url}")
        response = requests.get(geocoding_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data.get('features'):
                # Get the most relevant result (usually the first one)
                place = data['features'][0]
                address = place.get('place_name', 'Address not found')
                print(f"Address found: {address}")
                return address
            else:
                print("No address features found")
                return None
        else:
            print(f"Geocoding API error: {response.status_code}")
            return None

    except Exception as e:
        print(f"Error getting address: {str(e)}")
        return None

def send_detailed_pothole_report(email, detections, image_path, location, user_info=None, all_detections=None, all_images=None):
    """Send comprehensive pothole detection report via email with multiple images and detailed analysis"""
    print(f"send_detailed_pothole_report called - email: {email}, detections: {len(detections) if detections else 0}, email_enabled: {email_enabled}")
    print(f"Email config - EMAIL_USER: {EMAIL_USER}, EMAIL_PASSWORD: {'*' * len(EMAIL_PASSWORD) if EMAIL_PASSWORD else None}")

    if not email_enabled:
        print("Email not enabled - returning False")
        return False, "Email not configured"

    try:
        # Create secure email context
        context = ssl.create_default_context()

        # Create message container
        msg = MIMEMultipart()
        msg['Subject'] = 'Pothole Detection Report - Detailed Analysis'
        msg['From'] = EMAIL_USER
        msg['To'] = email

        # Current date and time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate detection statistics
        total_detections = 0
        highest_severity = 'Low'
        max_confidence = 0.0

        if all_detections:
            # Count all detections across all images
            for img_detections in all_detections:
                total_detections += len(img_detections)
                for detection in img_detections:
                    if detection.get('confidence', 0) > max_confidence:
                        max_confidence = detection['confidence']

                    # Determine highest severity
                    severity_levels = {'High': 3, 'Medium': 2, 'Low': 1}
                    current_severity = detection.get('severity', 'Low')
                    if severity_levels.get(current_severity, 1) > severity_levels.get(highest_severity, 1):
                        highest_severity = current_severity
        elif detections:
            # Fallback to single detection list
            total_detections = len(detections)
            for detection in detections:
                if detection.get('confidence', 0) > max_confidence:
                    max_confidence = detection['confidence']

                severity_levels = {'High': 3, 'Medium': 2, 'Low': 1}
                current_severity = detection.get('severity', 'Low')
                if severity_levels.get(current_severity, 1) > severity_levels.get(highest_severity, 1):
                    highest_severity = current_severity

        # Generate map and get address if location exists
        map_path = None
        detailed_address = None
        print(f"📍 Map generation debug - location: {location}")
        print(f"🗺️ MAPBOX_ACCESS_TOKEN available: {bool(MAPBOX_ACCESS_TOKEN)}")

        if location and location.get('latitude') and location.get('longitude') and MAPBOX_ACCESS_TOKEN:
            lat, lng = location['latitude'], location['longitude']
            print(f"🗺️ Generating map for coordinates: {lat}, {lng}")

            map_path = generate_static_map(lat, lng, highest_severity)
            print(f"🗺️ Map generation result: {map_path}")

            # Get detailed address
            detailed_address = get_address_from_coordinates(lat, lng)
            print(f"📍 Address lookup result: {detailed_address}")
        else:
            missing_items = []
            if not location: missing_items.append("location data")
            elif not location.get('latitude'): missing_items.append("latitude")
            elif not location.get('longitude'): missing_items.append("longitude")
            if not MAPBOX_ACCESS_TOKEN: missing_items.append("Mapbox token")
            print(f"❌ Map not generated - missing: {', '.join(missing_items)}")

        # Get user info for detailed report
        user_name = user_info.get('name', 'Unknown User') if user_info else 'Unknown User'
        user_email_raw = user_info.get('email', 'N/A') if user_info else 'N/A'

        # Clean user data - remove any pipe-separated metadata
        if '|' in user_name:
            user_name = user_name.split('|')[0].strip()
        if '|' in user_email_raw:
            user_email_raw = user_email_raw.split('|')[0].strip()

        user_email = user_email_raw

        # Create detailed email body without emojis
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: #f8f9fa; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; }}
                .header {{ background: linear-gradient(135deg, #2c3e50, #3498db); padding: 30px; text-align: center; color: white; }}
                .content {{ padding: 30px; }}
                .info-card {{ background: #f8f9fa; padding: 20px; margin: 15px 0; border-radius: 8px; border-left: 4px solid #3498db; }}
                .summary-card {{ background: #e8f4fd; padding: 20px; margin: 15px 0; border-radius: 8px; border: 1px solid #bee5eb; }}
                h1 {{ margin: 0; font-size: 28px; font-weight: 300; }}
                h2 {{ color: #2c3e50; margin-top: 0; font-size: 22px; }}
                h3 {{ color: #34495e; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; margin-bottom: 15px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 15px 0; background: white; }}
                th, td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; }}
                th {{ background-color: #f8f9fa; font-weight: 600; color: #495057; }}
                .severity-high {{ color: #dc3545; font-weight: bold; }}
                .severity-medium {{ color: #fd7e14; font-weight: bold; }}
                .severity-low {{ color: #28a745; font-weight: bold; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin: 20px 0; }}
                .stat-item {{ background: white; padding: 20px; text-align: center; border-radius: 8px; border: 1px solid #dee2e6; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: #2c3e50; display: block; }}
                .stat-label {{ color: #6c757d; font-size: 14px; margin-top: 5px; }}
                .image-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
                .image-item {{ text-align: center; }}
                .image-item img {{ max-width: 100%; border-radius: 8px; border: 2px solid #dee2e6; }}
                .image-title {{ font-weight: bold; margin: 10px 0 5px 0; color: #495057; }}
                .location-link {{ color: #3498db; text-decoration: none; font-weight: 500; }}
                .location-link:hover {{ text-decoration: underline; }}
                .footer {{ background: #ecf0f1; padding: 20px; text-align: center; color: #6c757d; font-size: 14px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="cid:logo_image" alt="FixMyPothole.AI Logo" style="width: 60px; height: 60px; margin-bottom: 15px; border-radius: 8px;">
                    <h1>Pothole Detection Report</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Professional AI-Powered Road Analysis</p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.8;">Report Generated: {current_time}</p>
                </div>

                <div class="content">
                    <div class="summary-card">
                        <h2>Detection Summary</h2>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-number">{total_detections}</span>
                                <div class="stat-label">Total Detections</div>
                            </div>
                            <div class="stat-item">
                                <span class="stat-number severity-{highest_severity.lower()}">{highest_severity}</span>
                                <div class="stat-label">Highest Severity</div>
                            </div>
                            <div class="stat-item">
                                <span class="stat-number">{max_confidence*100:.1f}%</span>
                                <div class="stat-label">Max Confidence</div>
                            </div>
                            <div class="stat-item">
                                <span class="stat-number">{len(all_images) if all_images else 1}</span>
                                <div class="stat-label">Images Analyzed</div>
                            </div>
                        </div>
                    </div>

                    <div class="info-card">
                        <h3>Reporter Information</h3>
                        <table>
                            <tr><td><strong>Name</strong></td><td>{user_name}</td></tr>
                            <tr><td><strong>Email</strong></td><td>{user_email}</td></tr>
                            <tr><td><strong>Report Time</strong></td><td>{current_time}</td></tr>
                        </table>
                    </div>

                    <div class="info-card">
                        <h3>Location Information</h3>
                        <table>
                            <tr><td><strong>Address</strong></td><td>{detailed_address if detailed_address else 'Address lookup not available'}</td></tr>
                            <tr><td><strong>GPS Coordinates</strong></td><td>{f"{location['latitude']:.6f}, {location['longitude']:.6f}" if location and location.get('latitude') and location.get('longitude') else 'Location data not available'}</td></tr>
                            <tr><td><strong>Accuracy</strong></td><td>{f"±{location.get('accuracy', 'Unknown')}m" if location and location.get('accuracy') else 'High precision GPS' if location else 'Unknown'}</td></tr>
                            <tr><td><strong>Map Link</strong></td><td>{f'<a href="https://www.google.com/maps?q={location["latitude"]},{location["longitude"]}" target="_blank" class="location-link">View on Google Maps</a>' if location and location.get('latitude') and location.get('longitude') else 'Not available'}</td></tr>
                        </table>
                    </div>

                    <div class="info-card">
                        <h3>Detection Results</h3>
                        {f"""
                        <table>
                            <thead>
                                <tr>
                                    <th>Image</th>
                                    <th>Detection</th>
                                    <th>Type</th>
                                    <th>Severity</th>
                                    <th>Confidence</th>
                                    <th>Relative Size</th>
                                </tr>
                            </thead>
                            <tbody>
                                {chr(10).join([
                                    f'''<tr>
                                        <td>#{img_idx + 1}</td>
                                        <td>#{det_idx + 1}</td>
                                        <td>{d.get('class', 'Pothole').title()}</td>
                                        <td><span class="severity-{d.get('severity', 'medium').lower()}">{d.get('severity', 'Medium')}</span></td>
                                        <td>{d.get('confidence', 0)*100:.1f}%</td>
                                        <td>{d.get('relative_size', 0)*100:.1f}%</td>
                                    </tr>'''
                                    for img_idx, img_detections in enumerate(all_detections or [detections] if detections else [])
                                    for det_idx, d in enumerate(img_detections)
                                ]) if (all_detections and any(len(img_dets) > 0 for img_dets in all_detections)) or detections else '<tr><td colspan="6" style="text-align: center; color: #28a745;">No potholes detected in the analyzed images</td></tr>'}
                            </tbody>
                        </table>
                        """ if (all_detections and any(len(img_dets) > 0 for img_dets in all_detections)) or detections else '<p style="text-align: center; color: #28a745; font-size: 16px; padding: 20px;">No potholes detected in the analyzed images</p>'}
                    </div>

                    {f'''
                    <div class="info-card">
                        <h3>Location Map</h3>
                        <div style="text-align: center; padding: 20px;">
                            <img src="cid:map_image" alt="Pothole location map" style="max-width: 100%; border-radius: 8px; border: 2px solid #dee2e6;">
                            <p style="margin-top: 15px; color: #6c757d; font-size: 14px;">
                                Precise Location: {location["latitude"]:.6f}, {location["longitude"]:.6f}
                            </p>
                        </div>
                    </div>
                    ''' if map_path else '''
                    <div class="info-card">
                        <h3>Location Map</h3>
                        <p style="text-align: center; color: #6c757d; padding: 20px;">
                            Location map not available - GPS coordinates may be missing or Mapbox service unavailable
                        </p>
                    </div>
                    '''}

                    <div class="info-card">
                        <h3>Analyzed Images</h3>
                        <div class="image-grid">
                            {chr(10).join([
                                f'''<div class="image-item">
                                    <div class="image-title">Image {i+1}</div>
                                    <img src="cid:detection_image_{i}" alt="Pothole analysis image {i+1}">
                                    <p style="color: #6c757d; font-size: 12px; margin-top: 8px;">AI-processed with detection overlay</p>
                                </div>'''
                                for i in range(len(all_images) if all_images else 1)
                            ]) if all_images and len(all_images) > 1 else '''
                            <div class="image-item">
                                <div class="image-title">Analysis Result</div>
                                <img src="cid:detection_image" alt="Pothole analysis result">
                                <p style="color: #6c757d; font-size: 12px; margin-top: 8px;">AI-processed with detection overlay</p>
                            </div>
                            '''}
                        </div>
                        <p style="text-align: center; color: #6c757d; font-size: 14px; margin-top: 20px; padding-top: 15px; border-top: 1px solid #dee2e6;">
                            Images analyzed using YOLOv8 machine learning model for pothole detection
                        </p>
                    </div>
                </div>

                <div class="footer">
                    <p><strong>FixMyPothole.AI</strong> - Professional Road Infrastructure Analysis</p>
                    <p>This report was generated automatically using artificial intelligence technology.</p>
                    <p>For questions or concerns, please contact your local road maintenance authority.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Attach HTML body
        msg.attach(MIMEText(body, 'html'))

        # Attach detection images
        if all_images and len(all_images) > 1:
            # Handle multiple base64 images
            for i, img_base64 in enumerate(all_images):
                try:
                    # Convert base64 to image data
                    if img_base64.startswith('data:image'):
                        img_base64 = img_base64.split(',')[1]

                    img_data = base64.b64decode(img_base64)
                    detection_img = MIMEImage(img_data, name=f"hazard_detection_{i+1}.jpg")
                    detection_img.add_header('Content-ID', f'<detection_image_{i}>')
                    msg.attach(detection_img)
                    print(f"Attached base64 image {i+1}")
                except Exception as e:
                    print(f"Failed to attach image {i+1}: {e}")
        else:
            # Attach single image (backward compatibility)
            if image_path and os.path.exists(image_path):
                print(f"Attaching detection image: {image_path}")
                with open(image_path, 'rb') as f:
                    img_data = f.read()

                detection_img = MIMEImage(img_data, name="hazard_detection.jpg")
                detection_img.add_header('Content-ID', '<detection_image>')
                msg.attach(detection_img)
                print("Detection image attached successfully")
            else:
                print(f"Detection image not attached - path: {image_path}, exists: {os.path.exists(image_path) if image_path else False}")

        # Attach logo image
        logo_path = os.path.join(os.path.dirname(__file__), '..', 'public', 'logo2.jpg')
        if os.path.exists(logo_path):
            print(f"Attaching logo image: {logo_path}")
            with open(logo_path, 'rb') as f:
                logo_data = f.read()

            logo_img = MIMEImage(logo_data, name="logo.jpg")
            logo_img.add_header('Content-ID', '<logo_image>')
            msg.attach(logo_img)
            print("Logo attached")
        else:
            print(f"Logo not found at: {logo_path}")

        # Attach map image if generated
        if map_path and os.path.exists(map_path):
            print(f"Attaching map image: {map_path}")
            with open(map_path, 'rb') as f:
                map_data = f.read()

            map_img = MIMEImage(map_data, name="hazard_map.png")
            map_img.add_header('Content-ID', '<map_image>')
            msg.attach(map_img)
            print("Map attached")
        else:
            print(f"Map not attached - path: {map_path}, exists: {os.path.exists(map_path) if map_path else False}")

        # Send email with SSL
        print(f"Attempting to send email to {email} via {SMTP_SERVER}:{SMTP_PORT}")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            print(f"Email successfully sent to {email}")

        return True, None
    except Exception as e:
        error_msg = f"Email sending failed: {str(e)}"
        app.logger.error(error_msg)
        traceback.print_exc()
        return False, error_msg

#  API ENDPOINTS FOR REACT INTEGRATION 

@app.route(f'{API_PREFIX}/health', methods=['GET'])
def api_health():
    """Health check endpoint for API status"""
    return jsonify(create_api_response(
        success=True,
        data={
            'status': 'healthy',
            'model_loaded': model is not None,
            'version': API_VERSION,
            'email_enabled': email_enabled,
            'endpoints': [
                f'{API_PREFIX}/health',
                f'{API_PREFIX}/detect',
                f'{API_PREFIX}/detect/batch',
                f'{API_PREFIX}/system/info'
            ]
        },
        message='Pothole Detection API is running'
    ))

@app.route(f'{API_PREFIX}/detect', methods=['POST'])
@require_api_key
def api_detect_potholes():
    """
    Main API endpoint for pothole detection
    Accepts: multipart/form-data with image file
    Returns: JSON with detection results
    """
    try:
        # Validate request
        if 'image' not in request.files:
            return jsonify(create_api_response(
                success=False,
                error='No image provided',
                code='MISSING_IMAGE'
            )), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify(create_api_response(
                success=False,
                error='No image selected',
                code='EMPTY_FILENAME'
            )), 400

        # Check file size (limit to 10MB)
        file.seek(0, 2)  # Seek to end of file
        file_size = file.tell()
        file.seek(0)  # Reset to beginning

        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return jsonify(create_api_response(
                success=False,
                error='File size too large. Maximum size is 10MB.',
                code='FILE_TOO_LARGE'
            )), 400

        # Get optional parameters
        email = request.form.get('email')
        send_email = request.form.get('send_email', 'false').lower() == 'true'
        include_image = request.form.get('include_image', 'true').lower() == 'true'

        # Get location data
        location = None
        try:
            latitude = request.form.get('latitude')
            longitude = request.form.get('longitude')
            print(f"Location debug - latitude: {latitude}, longitude: {longitude}")
            if latitude and longitude:
                location = {
                    'latitude': float(latitude),
                    'longitude': float(longitude)
                }
                print(f"Location parsed successfully: {location}")
            else:
                print("No location data provided")
        except (ValueError, TypeError) as e:
            print(f"Location parsing error: {e}")
            pass

        # Save uploaded image
        filename = secure_filename(f"api_detection_{uuid.uuid4().hex}.jpg")
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)

        # Process image
        img = PILImage.open(input_path)
        image_width, image_height = img.size

        # Run detection with higher confidence for better accuracy
        results = model(input_path, conf=max(CONFIDENCE_THRESHOLD, 0.3), imgsz=IMAGE_SIZE)
        detections = process_detection_results(results, image_width, image_height, input_path)

        print(f"Detection results: Found {len(detections)} detections")
        for i, det in enumerate(detections):
            print(f"  Detection {i+1}: {det['class']} (confidence: {det['confidence']:.3f}, severity: {det['severity']})")

        # Save annotated image if requested
        annotated_url = None
        annotated_path = None
        if include_image:
            annotated_filename = f"annotated_{filename}"
            annotated_path = os.path.join(OUTPUT_FOLDER, annotated_filename)

            # Save annotated image with detections drawn
            for r in results:
                # This saves the image with bounding boxes drawn
                annotated_img = r.plot()  # Get the annotated image
                import cv2
                cv2.imwrite(annotated_path, annotated_img)

            annotated_url = f'/static/outputs/{annotated_filename}'
            print(f"Annotated image saved to: {annotated_path}")
            print(f"Annotated image URL: {annotated_url}")

        # Get user information from request with validation
        user_name = request.form.get('user_name', 'Unknown User')
        user_email = request.form.get('user_email', 'N/A')

        # Basic input sanitization
        if user_name:
            user_name = user_name.strip()[:100]  # Limit length and trim whitespace
        if user_email:
            user_email = user_email.strip()[:100]  # Limit length and trim whitespace

        user_info = {
            'name': user_name,
            'email': user_email
        }

        # Extract additional multi-image data
        all_images_data = request.form.get('all_images')
        all_detections_data = request.form.get('all_detections')

        all_images = None
        all_detections = None

        try:
            if all_images_data:
                all_images = json.loads(all_images_data)
                print(f"Received {len(all_images)} images for multi-image email")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Invalid all_images data: {e}")

        try:
            if all_detections_data:
                all_detections = json.loads(all_detections_data)
                print(f"Received detections for {len(all_detections)} images")
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Invalid all_detections data: {e}")

        # Send email if requested and detections found
        email_sent = False
        email_error = None

        print(f"Email debug - send_email: {send_email}, email: {email}, detections_count: {len(detections)}, email_enabled: {email_enabled}")
        print(f"Email debug - all_images: {len(all_images) if all_images else 0}, all_detections: {len(all_detections) if all_detections else 0}")

        # Send email if requested (regardless of detections for comprehensive reporting)
        if send_email and email and email_enabled:
            # Clean the admin email address - remove any pipe-separated metadata
            clean_admin_email = email.split('|')[0].strip() if '|' in email else email.strip()
            print(f"Sending admin email to: {clean_admin_email}")
            email_sent, email_error = send_detailed_pothole_report(
                clean_admin_email, detections, annotated_path if include_image else None, location, user_info, all_detections, all_images
            )
            print(f"Admin email result - sent: {email_sent}, error: {email_error}")

            # Also send to user email if different from admin email
            user_email_raw = user_info.get('email') if user_info else None

            # Clean the user email address - remove any pipe-separated metadata
            user_email = None
            if user_email_raw and user_email_raw != 'N/A':
                # Extract just the email address part (before any pipe character)
                user_email = user_email_raw.split('|')[0].strip() if '|' in user_email_raw else user_email_raw.strip()

            print(f"User email check - user_email: {user_email}, admin_email: {clean_admin_email}")

            if user_email and user_email != clean_admin_email and user_email != 'N/A' and '@' in user_email:
                try:
                    print(f"Sending user email to: {user_email}")
                    user_email_sent, user_email_error = send_detailed_pothole_report(
                        user_email, detections, annotated_path if include_image else None, location, user_info, all_detections, all_images
                    )
                    print(f"User email result - sent: {user_email_sent}, error: {user_email_error}")
                except Exception as user_email_error:
                    print(f"Failed to send user email to {user_email}: {user_email_error}")
        else:
            print(f"Email not sent - Reason: send_email={send_email}, email={bool(email)}, email_enabled={email_enabled}")

        # Prepare response data
        response_data = {
            'detections': detections,
            'detection_count': len(detections),
            'image_info': {
                'width': image_width,
                'height': image_height,
                'filename': filename
            },
            'processing_info': {
                'confidence_threshold': CONFIDENCE_THRESHOLD,
                'image_size': IMAGE_SIZE,
                'model_path': MODEL_PATH
            }
        }

        if include_image and annotated_url:
            response_data['annotated_image_url'] = annotated_url

        if location:
            response_data['location'] = location

        if send_email:
            response_data['email'] = {
                'sent': email_sent,
                'error': email_error,
                'recipient': email if email_sent else None
            }

        # Clean up original uploaded file
        try:
            os.remove(input_path)
        except OSError as e:
            print(f"Warning: Could not remove temporary file {input_path}: {e}")

        return jsonify(create_api_response(
            success=True,
            data=response_data,
            message=f'Detection completed. Found {len(detections)} pothole(s).'
        ))

    except Exception as e:
        app.logger.error(f"API Detection error: {str(e)}")
        return jsonify(create_api_response(
            success=False,
            error=str(e),
            code='DETECTION_ERROR'
        )), 500

@app.route(f'{API_PREFIX}/detect/batch', methods=['POST'])
@require_api_key
def api_batch_detect():
    """
    Batch detection endpoint for multiple images
    Accepts: multipart/form-data with multiple image files
    Returns: JSON with batch detection results
    """
    try:
        files = request.files.getlist('images')
        if not files or len(files) == 0:
            return jsonify(create_api_response(
                success=False,
                error='No images provided',
                code='MISSING_IMAGES'
            )), 400

        batch_results = []
        total_detections = 0

        for i, file in enumerate(files):
            if file.filename == '':
                continue

            try:
                # Save uploaded image
                filename = secure_filename(f"batch_{i}_{uuid.uuid4().hex}.jpg")
                input_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(input_path)

                # Process image
                img = PILImage.open(input_path)
                image_width, image_height = img.size

                # Run detection
                results = model(input_path, conf=CONFIDENCE_THRESHOLD, imgsz=IMAGE_SIZE)
                detections = process_detection_results(results, image_width, image_height, input_path)

                batch_results.append({
                    'filename': file.filename,
                    'detections': detections,
                    'detection_count': len(detections),
                    'image_info': {
                        'width': image_width,
                        'height': image_height
                    }
                })

                total_detections += len(detections)

                # Clean up
                os.remove(input_path)

            except Exception as e:
                batch_results.append({
                    'filename': file.filename,
                    'error': str(e),
                    'detections': [],
                    'detection_count': 0
                })

        return jsonify(create_api_response(
            success=True,
            data={
                'batch_results': batch_results,
                'summary': {
                    'total_images': len(files),
                    'processed_images': len(batch_results),
                    'total_detections': total_detections
                }
            },
            message=f'Batch processing completed. {total_detections} total detections found.'
        ))

    except Exception as e:
        app.logger.error(f"Batch detection error: {str(e)}")
        return jsonify(create_api_response(
            success=False,
            error=str(e),
            code='BATCH_DETECTION_ERROR'
        )), 500

@app.route(f'{API_PREFIX}/system/info', methods=['GET'])
@require_api_key
def api_system_info():
    """Get system information and configuration"""
    return jsonify(create_api_response(
        success=True,
        data={
            'model_info': {
                'path': MODEL_PATH,
                'confidence_threshold': CONFIDENCE_THRESHOLD,
                'image_size': IMAGE_SIZE,
                'classes': list(model.names.values()) if model else []
            },
            'email_config': {
                'enabled': email_enabled,
                'smtp_server': SMTP_SERVER,
                'smtp_port': SMTP_PORT
            },
            'api_info': {
                'version': API_VERSION,
                'authentication_required': bool(config['API_KEY'])
            }
        }
    ))

@app.route(f'{API_PREFIX}/generate-description', methods=['POST'])
def generate_description():
    """Generate AI-powered description for pothole image"""
    try:
        if not gemini_enabled:
            return jsonify({
                'success': False,
                'error': 'Gemini AI is not available. Please check API key configuration.'
            }), 503

        # Get image from request
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image provided'
            }), 400

        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No image selected'
            }), 400

        # Get optional location data
        location_data = request.form.get('location', '{}')
        try:
            location = json.loads(location_data)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Warning: Invalid location data: {e}")
            location = {}

        # Process image
        image_bytes = image_file.read()
        image = PILImage.open(io.BytesIO(image_bytes))

        # Prepare prompt for Gemini
        prompt = f"""
        Analyze this road image for potholes and road damage. Provide a professional report description including:

        1. Damage Assessment: Describe the type and extent of road damage visible
        2. Severity Level: Rate as High, Medium, or Low based on size and depth
        3. Safety Impact: Explain potential risks to vehicles and pedestrians
        4. Location Context: Describe the road type and surrounding area
        5. Repair Urgency: Recommend priority level for repairs
        6. Future Prediction: Predict the weather of that location and future of the potholes increment or decrement.
        Start every point's paragragh with a new line
        Location context: {location.get('address', 'Location not specified')}

        Format the response as a clear, professional report suitable for government authorities.
        Keep it concise but comprehensive (2 paragraphs).
        """

        # Generate description using Gemini with retry logic
        max_retries = 3
        retry_delay = 2  # seconds

        for attempt in range(max_retries):
            try:
                # Try main model first, then fallback model if available
                current_model = gemini_model
                if attempt > 0 and gemini_fallback_model:
                    current_model = gemini_fallback_model
                    print(f"Using fallback model on attempt {attempt + 1}")

                response = current_model.generate_content([prompt, image])

                if response.text:
                    return jsonify({
                        'success': True,
                        'description': response.text.strip(),
                        'generated_at': datetime.now().isoformat()
                    })
                else:
                    raise Exception("Empty response from Gemini")

            except Exception as gemini_error:
                error_message = str(gemini_error).lower()

                # Handle specific Gemini errors
                if '503' in error_message or 'overloaded' in error_message:
                    if attempt < max_retries - 1:
                        print(f"Gemini overloaded, retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                        import time
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'Gemini AI is currently overloaded. Please try again in a few minutes.',
                            'error_type': 'overloaded'
                        }), 503

                elif 'timeout' in error_message:
                    return jsonify({
                        'success': False,
                        'error': 'AI description generation timed out. Please try again.',
                        'error_type': 'timeout'
                    }), 408

                elif 'quota' in error_message or 'limit' in error_message:
                    return jsonify({
                        'success': False,
                        'error': 'Daily AI quota exceeded. Please try again tomorrow.',
                        'error_type': 'quota_exceeded'
                    }), 429

                else:
                    # Generic error
                    if attempt < max_retries - 1:
                        print(f"Gemini error, retrying... (attempt {attempt + 1}/{max_retries}): {gemini_error}")
                        import time
                        time.sleep(1)
                        continue
                    else:
                        return jsonify({
                            'success': False,
                            'error': f'AI description generation failed: {str(gemini_error)}',
                            'error_type': 'generation_failed'
                        }), 500

        # This shouldn't be reached, but just in case
        return jsonify({
            'success': False,
            'error': 'Failed to generate description after multiple attempts'
        }), 500

    except Exception as e:
        print(f"Error generating description: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to generate description: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Verify environment variables
    print("\n" + "="*50)
    print("Starting Pothole Detection System")
    print("="*50)
    print(f"Model path: {MODEL_PATH}")
    print(f"Email enabled: {email_enabled}")
    if email_enabled:
        print(f"Email user: {EMAIL_USER}")
        print(f"SMTP server: {SMTP_SERVER}:{SMTP_PORT}")
    print(f"Mapbox enabled: {bool(MAPBOX_ACCESS_TOKEN)}")
    if MAPBOX_ACCESS_TOKEN:
        print(f"Mapbox token: {'*' * len(MAPBOX_ACCESS_TOKEN)}")
    print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print(f"Image size: {IMAGE_SIZE}")
    print(f"API version: {API_VERSION}")
    print("="*50)

    app.run(host='0.0.0.0', port=5000, debug=True)

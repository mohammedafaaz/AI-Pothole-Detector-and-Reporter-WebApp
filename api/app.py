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

# Note: Database imports removed - using localStorage only

# Initialize Flask app
app = Flask(__name__, static_url_path='/static')

# Enable CORS for React frontend
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000', 'http://localhost:5173'])

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
    'API_KEY': os.getenv('API_KEY', None)  # Optional API key for authentication
}

# Print configuration for debugging
print("\nConfiguration values:")
for key, value in config.items():
    if key in ['EMAIL_PASSWORD', 'MAPBOX_ACCESS_TOKEN'] and value:
        print(f"{key}: {'*' * len(value)}")
    else:
        print(f"{key}: {value}")

# Check for required values (only MODEL_PATH is required)
missing_config = [key for key in ['MODEL_PATH'] if not config[key]]
if missing_config:
    print(f"\nERROR: Missing required configuration: {', '.join(missing_config)}")
    print("Please set these values in your .env file")
    sys.exit(1)

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

# API Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
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

def send_email_with_results(email, detections, image_path, location, user_info=None):
    """Send detection results via email with static map"""
    print(f"send_email_with_results called - email: {email}, detections: {len(detections)}, email_enabled: {email_enabled}")

    if not email_enabled:
        print("Email not enabled - returning False")
        return False, "Email not configured"

    try:
        # Create secure email context
        context = ssl.create_default_context()

        # Create message container
        msg = MIMEMultipart()
        msg['Subject'] = '🚧 Pothole Detection Alert'
        msg['From'] = EMAIL_USER
        msg['To'] = email

        # Current date and time
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Get highest severity for map marker
        severity = 'Medium'
        if detections:
            severity_levels = {'High': 3, 'Medium': 2, 'Low': 1}
            highest_severity = max(detections, key=lambda x: severity_levels[x['severity']])
            severity = highest_severity['severity']

        # Generate map and get address if location exists
        map_path = None
        detailed_address = None
        print(f"📍 Map generation debug - location: {location}")
        print(f"🗺️ MAPBOX_ACCESS_TOKEN available: {bool(MAPBOX_ACCESS_TOKEN)}")

        if location and location.get('latitude') and location.get('longitude') and MAPBOX_ACCESS_TOKEN:
            lat, lng = location['latitude'], location['longitude']
            print(f"🗺️ Generating map for coordinates: {lat}, {lng}")

            map_path = generate_static_map(lat, lng, severity)
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
        user_email = user_info.get('email', 'N/A') if user_info else 'N/A'

        # Create detailed email body
        body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ padding: 30px; text-align: center; color: white; }}
                .content {{ padding: 30px; background: #f8f9fa; }}
                .info-card {{ background: white; padding: 20px; margin: 15px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ margin: 0; font-size: 28px; }}
                h2 {{ color: #dc3545; margin-top: 0; }}
                h3 {{ color: #495057; border-bottom: 2px solid #dee2e6; padding-bottom: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #dee2e6; padding: 12px; text-align: left; }}
                th {{ background-color: #e9ecef; font-weight: bold; }}
                .high {{ color: #dc3545; font-weight: bold; }}
                .medium {{ color: #fd7e14; font-weight: bold; }}
                .low {{ color: #28a745; font-weight: bold; }}
                .map-container {{ margin: 20px 0; text-align: center; }}
                img {{ max-width: 100%; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); }}
                .footer {{ margin-top: 30px; text-align: center; color: #6c757d; font-size: 0.9em; padding: 20px; background: #e9ecef; }}
                .stats {{ display: flex; justify-content: space-around; text-align: center; }}
                .stat {{ background: white; padding: 15px; border-radius: 8px; }}
                .badge {{ display: inline-block; padding: 5px 10px; border-radius: 15px; font-size: 12px; font-weight: bold; }}
                .badge-high {{ background: #dc3545; color: white; }}
                .badge-medium {{ background: #fd7e14; color: white; }}
                .badge-low {{ background: #28a745; color: white; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div style="text-align: center; margin-bottom: 20px;">
                    <img src="cid:logo_image" alt="FixMyPothole.AI Logo" style="width: 80px; height: 80px; object-fit: contain; border-radius: 10px;">
                </div>
                <h1>FixMyPothole.AI Detection Report</h1>
                <p>AI-Powered Pothole Detection & Analysis</p>
                <p style="font-size: 14px; opacity: 0.9;">Generated on {current_time}</p>
            </div>

            <div class="content">
                <div class="info-card">
                    <h2>Detection Summary</h2>
                    <div class="stats">
                        <div class="stat">
                            <strong>{len(detections)}</strong><br>
                            <small>Potholes Found</small>
                        </div>
                        <div class="stat">
                            <strong>{severity}</strong><br>
                            <small>Highest Severity</small>
                        </div>
                        <div class="stat">
                            <strong>{max([d['confidence'] for d in detections], default=0)*100:.1f}%</strong><br>
                            <small>Max Confidence</small>
                        </div>
                    </div>
                </div>

                <div class="info-card">
                    <h3>Reporter Information</h3>
                    <p><strong>Name:</strong> {user_name}</p>
                    <p><strong>Email:</strong> {user_email}</p>
                    <p><strong>Report Time:</strong> {current_time}</p>
                </div>

                <div class="info-card">
                    <h3>📍 Location Details</h3>
                    {f"<p><strong>📍 Address:</strong> {detailed_address}</p>" if detailed_address else "<p><strong>📍 Address:</strong> <em>Address lookup not available</em></p>"}
                    <p><strong>🌐 GPS Coordinates:</strong> {f"{location['latitude']:.6f}, {location['longitude']:.6f}" if location and location.get('latitude') and location.get('longitude') else '<span style="color: #dc3545;">⚠️ Location data not available - GPS may have been disabled</span>'}</p>
                    {f"<p><strong>🎯 Precision:</strong> ±{location.get('accuracy', 'Unknown')}m accuracy</p>" if location and location.get('accuracy') else "<p><strong>🎯 Precision:</strong> High precision GPS data</p>" if location else "<p><strong>🎯 Precision:</strong> <em>Location precision unknown</em></p>"}
                    {f"<p><strong>🗺️ Map Link:</strong> <a href='https://www.google.com/maps?q={location['latitude']},{location['longitude']}' target='_blank' style='color: #007bff; text-decoration: none;'>📍 View on Google Maps</a></p>" if location and location.get('latitude') and location.get('longitude') else "<p><strong>🗺️ Map Link:</strong> <em>Not available without GPS coordinates</em></p>"}
                </div>

                <div class="info-card">
                    <h3>Detected Hazards</h3>
                    {"<p style='text-align: center; color: #28a745; font-size: 18px;'>❌ No Potholes detected in this image</p>" if not detections else f"""
                    <table>
                        <tr>
                            <th>Detection #</th>
                            <th>Type</th>
                            <th>Severity</th>
                            <th>Confidence</th>
                            <th>Size</th>
                        </tr>
                        {chr(10).join([
                            f'''<tr>
                                <td>#{i+1}</td>
                                <td>{d['class'].title()}</td>
                                <td><span class="badge badge-{d['severity'].lower()}">{d['severity']}</span></td>
                                <td>{d['confidence']*100:.1f}%</td>
                                <td>{d.get('relative_size', 0)*100:.1f}% of image</td>
                            </tr>''' for i, d in enumerate(detections)
                        ])}
                    </table>
                    """}
                </div>

                <div class="info-card map-container">
                    <h3>📍 Location Map</h3>
                    {f'<img src="cid:map_image" alt="Pothole location map" style="border: 3px solid #dee2e6; max-width: 100%; height: auto;">' if map_path else '<p style="color: #6c757d;">📍 Location map not available - GPS coordinates may be missing</p>'}
                    {f'<p style="margin-top: 10px; color: #6c757d; font-size: 14px;">📍 Exact location: {location["latitude"]:.6f}, {location["longitude"]:.6f}</p>' if location else ''}
                </div>

                <div class="info-card map-container">
                    <h3>Model Detected Image</h3>
                    <img src="cid:detection_image" alt="AI-analyzed pothole detection" style="border: 3px solid #007bff;">
                    <p style="margin-top: 10px; color: #6c757d; font-size: 14px;">
                        Image processed using YOLOv8 machine learning model
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        # Attach HTML body
        msg.attach(MIMEText(body, 'html'))

        # Attach detection image
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

        # Get user information from request
        user_info = {
            'name': request.form.get('user_name', 'Unknown User'),
            'email': request.form.get('user_email', 'N/A')
        }

        # Send email if requested and detections found
        email_sent = False
        email_error = None

        print(f"Email debug - send_email: {send_email}, email: {email}, detections_count: {len(detections)}, email_enabled: {email_enabled}")

        if send_email and email and detections and email_enabled:  # Only send if potholes detected
            print(f"Sending admin email to: {email}")
            email_sent, email_error = send_email_with_results(
                email, detections, annotated_path if include_image else None, location, user_info
            )
            print(f"Admin email result - sent: {email_sent}, error: {email_error}")

            # Also send to user email if different from admin email
            user_email = user_info.get('email') if user_info else None
            print(f"User email check - user_email: {user_email}, admin_email: {email}")

            if user_email and user_email != email and user_email != 'N/A' and '@' in user_email:
                try:
                    print(f"Sending user email to: {user_email}")
                    user_email_sent, user_email_error = send_email_with_results(
                        user_email, detections, annotated_path if include_image else None, location, user_info
                    )
                    print(f"User email result - sent: {user_email_sent}, error: {user_email_error}")
                except Exception as user_email_error:
                    print(f"Failed to send user email to {user_email}: {user_email_error}")
        else:
            print(f"Email not sent - Reason: send_email={send_email}, email={bool(email)}, detections={len(detections)}, email_enabled={email_enabled}")

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
        except:
            pass

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

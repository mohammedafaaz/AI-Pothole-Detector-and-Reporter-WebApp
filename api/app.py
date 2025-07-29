from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import cv2
import os
import math
import uuid
import requests
from datetime import datetime
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
from email_service import EmailService

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
    'CONFIDENCE_THRESHOLD': float(os.getenv('CONFIDENCE_THRESHOLD', 0.25)),
    'IMAGE_SIZE': int(os.getenv('IMAGE_SIZE', 640)),
    'MAPBOX_ACCESS_TOKEN': os.getenv('MAPBOX_ACCESS_TOKEN', ''),
    'API_KEY': os.getenv('API_KEY', None),  # Optional API key for authentication
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),  # Gemini API key
    'EMAIL_USER': os.getenv('EMAIL_USER', ''),
    'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD', ''),
    'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'SMTP_PORT': int(os.getenv('SMTP_PORT', 587)),
    'ADMIN_EMAIL': os.getenv('ADMIN_EMAIL', '')
}

# Initialize Gemini AI with enhanced debugging
gemini_enabled = False
gemini_model = None
gemini_fallback_model = None

# Enhanced debugging for Railway deployment
print("🔍 Gemini API Initialization Debug:")
print(f"   Environment: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'Local'}")
print(f"   API Key Present: {'Yes' if config['GEMINI_API_KEY'] else 'No'}")
if config['GEMINI_API_KEY']:
    print(f"   API Key Length: {len(config['GEMINI_API_KEY'])}")
    print(f"   API Key Prefix: {config['GEMINI_API_KEY'][:10]}...")

if config['GEMINI_API_KEY']:
    try:
        print("🔧 Configuring Gemini API...")
        genai.configure(api_key=config['GEMINI_API_KEY'])

        print("🤖 Initializing primary model (gemini-1.5-flash)...")
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')

        # Test the model with a simple request
        print("🧪 Testing Gemini API connection...")
        test_response = gemini_model.generate_content("Hello, respond with 'API Working'")
        if test_response and test_response.text:
            print(f"✅ Gemini API test successful: {test_response.text.strip()}")
        else:
            print("⚠️ Gemini API test returned empty response")

        # Initialize fallback model
        try:
            print("🔄 Initializing fallback model...")
            gemini_fallback_model = genai.GenerativeModel('gemini-1.0-pro-vision-latest')
            print("✅ Gemini AI initialized with fallback model")
        except Exception as e:
            print(f"⚠️ Fallback model not available: {e}")

        gemini_enabled = True
        print("✅ Gemini AI initialized successfully")

    except Exception as e:
        print(f"❌ Gemini AI initialization failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error details: {str(e)}")

        # Check for specific error types
        if "API_KEY" in str(e).upper():
            print("🔑 Issue appears to be API key related")
        elif "QUOTA" in str(e).upper() or "LIMIT" in str(e).upper():
            print("📊 Issue appears to be quota/rate limit related")
        elif "NETWORK" in str(e).upper() or "CONNECTION" in str(e).upper():
            print("🌐 Issue appears to be network/connection related")

        gemini_enabled = False
else:
    print("⚠️ Gemini API key not provided - AI descriptions disabled")
    print("   Set GEMINI_API_KEY environment variable to enable AI features")
    gemini_enabled = False

# Print configuration for debugging
print("\nConfiguration values:")
for key, value in config.items():
    if key in ['EMAIL_PASSWORD', 'MAPBOX_ACCESS_TOKEN', 'GEMINI_API_KEY'] and value:
        print(f"{key}: {'*' * len(value)}")
    else:
        print(f"{key}: {value}")

# Print email configuration status
email_enabled = bool(config['EMAIL_USER'] and config['EMAIL_PASSWORD'])
print(f"Email service enabled: {email_enabled}")
if email_enabled:
    print(f"SMTP server: {config['SMTP_SERVER']}:{config['SMTP_PORT']}")
    print(f"Admin email: {config['ADMIN_EMAIL']}")
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

# Extract configuration
MODEL_PATH = config['MODEL_PATH']
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




#  API ENDPOINTS FOR REACT INTEGRATION 

@app.route(f'{API_PREFIX}/health', methods=['GET'])
def api_health():
    """Health check endpoint for API status"""
    return jsonify(create_api_response(
        success=True,
        data={
            'status': 'healthy',
            'model_loaded': model is not None,
            'gemini_enabled': gemini_enabled,
            'version': API_VERSION,
            'environment': os.getenv('RAILWAY_ENVIRONMENT', 'local'),
            'endpoints': [
                f'{API_PREFIX}/health',
                f'{API_PREFIX}/detect',
                f'{API_PREFIX}/detect/batch',
                f'{API_PREFIX}/send-report-email',
                f'{API_PREFIX}/system/info',
                f'{API_PREFIX}/generate-description'
            ]
        },
        message='Pothole Detection API is running'
    ))

@app.route(f'{API_PREFIX}/debug/gemini', methods=['GET'])
def debug_gemini():
    """Debug endpoint for Gemini API status - Railway deployment diagnostics"""
    try:
        debug_info = {
            'environment': os.getenv('RAILWAY_ENVIRONMENT', 'local'),
            'gemini_enabled': gemini_enabled,
            'gemini_model_available': gemini_model is not None,
            'gemini_fallback_available': gemini_fallback_model is not None,
            'api_key_configured': bool(config.get('GEMINI_API_KEY')),
            'api_key_length': len(config.get('GEMINI_API_KEY', '')) if config.get('GEMINI_API_KEY') else 0,
            'python_version': os.sys.version,
            'environment_variables': {
                'RAILWAY_ENVIRONMENT': os.getenv('RAILWAY_ENVIRONMENT'),
                'RAILWAY_PROJECT_ID': os.getenv('RAILWAY_PROJECT_ID'),
                'RAILWAY_SERVICE_ID': os.getenv('RAILWAY_SERVICE_ID'),
                'PORT': os.getenv('PORT'),
            }
        }

        # Test Gemini API if available
        if gemini_enabled and gemini_model:
            try:
                test_response = gemini_model.generate_content("Test connection - respond with 'OK'")
                debug_info['gemini_test'] = {
                    'success': True,
                    'response': test_response.text.strip() if test_response and test_response.text else 'Empty response'
                }
            except Exception as e:
                debug_info['gemini_test'] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
        else:
            debug_info['gemini_test'] = {
                'success': False,
                'error': 'Gemini not enabled or model not available'
            }

        return jsonify(create_api_response(
            success=True,
            data=debug_info,
            message='Gemini debug information'
        ))

    except Exception as e:
        return jsonify(create_api_response(
            success=False,
            error=f'Debug endpoint failed: {str(e)}',
            code='DEBUG_ERROR'
        )), 500

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
            try:
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

                # Schedule cleanup for annotated image too
                import threading
                cleanup_thread_annotated = threading.Timer(10.0, cleanup_file, args=[annotated_path])
                cleanup_thread_annotated.start()

            except Exception as e:
                print(f"Warning: Could not save annotated image: {e}")
                annotated_url = None
                annotated_path = None

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



        # Clean up original uploaded file (with proper timing)
        def cleanup_file(file_path):
            """Safely cleanup temporary file with retry logic"""
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"Successfully removed temporary file: {file_path}")
                    break
                except OSError as e:
                    if attempt < max_retries - 1:
                        print(f"Attempt {attempt + 1}: Could not remove {file_path}, retrying in 1 second...")
                        time.sleep(1)
                    else:
                        print(f"Warning: Could not remove temporary file {file_path} after {max_retries} attempts: {e}")

        # Schedule cleanup for later (after potential email processing)
        import threading
        cleanup_thread = threading.Timer(5.0, cleanup_file, args=[input_path])
        cleanup_thread.start()

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

                # Clean up with proper timing
                def cleanup_batch_file(file_path):
                    """Safely cleanup batch file"""
                    import time
                    max_retries = 3
                    for attempt in range(max_retries):
                        try:
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            break
                        except OSError as e:
                            if attempt < max_retries - 1:
                                time.sleep(0.5)
                            else:
                                print(f"Warning: Could not remove batch file {file_path}: {e}")

                # Schedule cleanup
                import threading
                cleanup_thread = threading.Timer(2.0, cleanup_batch_file, args=[input_path])
                cleanup_thread.start()

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

            'api_info': {
                'version': API_VERSION,
                'authentication_required': bool(config['API_KEY'])
            }
        }
    ))

@app.route(f'{API_PREFIX}/generate-description', methods=['POST'])
def generate_description():
    """Generate AI-powered description for pothole image with enhanced debugging"""
    try:
        # Enhanced debugging for Railway deployment
        print(f"🔍 Description request received")
        print(f"   Environment: {'Railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'Local'}")
        print(f"   Gemini Enabled: {gemini_enabled}")
        print(f"   Gemini Model Available: {gemini_model is not None}")

        if not gemini_enabled:
            error_msg = 'Gemini AI is not available. Please check API key configuration.'
            print(f"❌ {error_msg}")
            return jsonify({
                'success': False,
                'error': error_msg,
                'debug_info': {
                    'gemini_enabled': gemini_enabled,
                    'api_key_present': bool(config.get('GEMINI_API_KEY')),
                    'environment': os.getenv('RAILWAY_ENVIRONMENT', 'local')
                }
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
        Analyze this road image and provide a concise professional report. Format with clear sections:

        **Damage Assessment:**
        [Describe type and extent of road damage in 1-2 sentences]

        **Severity Level:**
        [Rate as High/Medium/Low with brief justification]

        **Safety Impact:**
        [Explain risks to vehicles/pedestrians in 1 sentence]

        **Location Context:**
        [Describe road type and area in 1 sentence]

        **Repair Priority:**
        [Recommend Immediate/Urgent/Routine with timeline]

        Location: {location.get('address', 'Location not specified')}

        Keep each section to 1-2 sentences maximum. Use bullet points or short paragraphs.
        Format with clear line breaks between sections for readability.
        """

        # Generate description using Gemini with enhanced retry logic
        max_retries = 3
        retry_delay = 2  # seconds

        print(f"🤖 Starting Gemini description generation...")
        print(f"   Max retries: {max_retries}")
        print(f"   Image size: {len(image_bytes)} bytes")

        for attempt in range(max_retries):
            try:
                print(f"🔄 Attempt {attempt + 1}/{max_retries}")

                # Try main model first, then fallback model if available
                current_model = gemini_model
                model_name = "gemini-1.5-flash"

                if attempt > 0 and gemini_fallback_model:
                    current_model = gemini_fallback_model
                    model_name = "gemini-1.0-pro-vision-latest"
                    print(f"   Using fallback model: {model_name}")
                else:
                    print(f"   Using primary model: {model_name}")

                print(f"   Sending request to Gemini...")
                response = current_model.generate_content([prompt, image])
                print(f"   Received response from Gemini")

                if response and response.text:
                    response_text = response.text.strip()
                    print(f"✅ Gemini response successful (length: {len(response_text)})")
                    return jsonify({
                        'success': True,
                        'description': response_text,
                        'generated_at': datetime.now().isoformat(),
                        'model_used': model_name,
                        'attempt': attempt + 1
                    })
                else:
                    error_msg = "Empty response from Gemini"
                    print(f"⚠️ {error_msg}")
                    raise Exception(error_msg)

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



@app.route(f'{API_PREFIX}/test-gemini', methods=['POST'])
@require_api_key
def test_gemini():
    """
    Test endpoint to manually test Gemini responses
    """
    try:
        if not gemini_model:
            return jsonify(create_api_response(
                success=False,
                error='Gemini AI service not available',
                code='GEMINI_UNAVAILABLE'
            )), 503

        # Get uploaded file
        if 'image' not in request.files:
            return jsonify(create_api_response(
                success=False,
                error='No image provided',
                code='NO_IMAGE'
            )), 400

        file = request.files['image']
        if file.filename == '':
            return jsonify(create_api_response(
                success=False,
                error='No valid image provided',
                code='INVALID_IMAGE'
            )), 400

        # Process image
        image_bytes = file.read()
        image = PILImage.open(io.BytesIO(image_bytes))

        # Simple test prompt
        test_prompt = """
        Look at this image and tell me:
        1. Is this a road or traffic-related scene?
        2. Do you see any hazards, damage, accidents, or safety concerns?
        3. What specifically do you observe?

        Be detailed in your response.
        """

        # Send to Gemini
        response = gemini_model.generate_content([test_prompt, image])
        gemini_text = response.text.strip()

        return jsonify(create_api_response(
            success=True,
            data={
                'gemini_response': gemini_text,
                'image_filename': file.filename
            },
            message='Gemini test completed successfully'
        ))

    except Exception as e:
        print(f"Error in Gemini test: {e}")
        traceback.print_exc()
        return jsonify(create_api_response(
            success=False,
            error=f'Gemini test failed: {str(e)}',
            code='GEMINI_TEST_ERROR'
        )), 500

@app.route(f'{API_PREFIX}/send-report-email', methods=['POST'])
@require_api_key
def send_report_email():
    """
    Send pothole report email to user and administrator
    This endpoint is called after a report is successfully submitted
    """
    try:
        # Get request data
        data = request.get_json()

        if not data:
            return jsonify(create_api_response(
                success=False,
                error='No data provided',
                code='MISSING_DATA'
            )), 400

        # Extract required fields
        user_email = data.get('user_email')
        user_name = data.get('user_name', 'Unknown User')
        detections_data = data.get('detections_data', [])
        location_data = data.get('location_data', {})
        images_data = data.get('images_data', [])

        # Debug logging for image data
        print(f"Email endpoint received:")
        print(f"  - User email: {user_email}")
        print(f"  - Images count: {len(images_data)}")
        for i, img_data in enumerate(images_data):
            if img_data:
                print(f"  - Image {i+1}: {len(str(img_data))} characters, starts with: {str(img_data)[:50]}...")
            else:
                print(f"  - Image {i+1}: EMPTY or None")
        print(f"  - Detections count: {len(detections_data)}")

        # Validate required fields
        if not user_email:
            return jsonify(create_api_response(
                success=False,
                error='User email is required',
                code='MISSING_USER_EMAIL'
            )), 400

        if not images_data:
            return jsonify(create_api_response(
                success=False,
                error='At least one image is required',
                code='MISSING_IMAGES'
            )), 400

        # Initialize email service
        try:
            email_service = EmailService()
        except ValueError as e:
            return jsonify(create_api_response(
                success=False,
                error=f'Email service configuration error: {str(e)}',
                code='EMAIL_CONFIG_ERROR'
            )), 500

        # Send emails (with small delay to ensure file operations are complete)
        import time
        time.sleep(0.5)  # Small delay to prevent file access conflicts

        success, error_message = email_service.send_pothole_report(
            user_email=user_email,
            user_name=user_name,
            detections_data=detections_data,
            location_data=location_data,
            images_data=images_data
        )

        if success:
            return jsonify(create_api_response(
                success=True,
                data={
                    'email_sent': True,
                    'recipients': [email_service.admin_email]
                },
                message='Report email sent successfully to administrator'
            ))
        else:
            return jsonify(create_api_response(
                success=False,
                error=f'Failed to send emails: {error_message}',
                code='EMAIL_SEND_FAILED'
            )), 500

    except Exception as e:
        logger.error(f"Error in send_report_email: {str(e)}")
        return jsonify(create_api_response(
            success=False,
            error=f'Internal server error: {str(e)}',
            code='INTERNAL_ERROR'
        )), 500

if __name__ == '__main__':
    # Verify environment variables
    print("\n" + "="*50)
    print("Starting Pothole Detection System")
    print("="*50)
    print(f"Model path: {MODEL_PATH}")
    print(f"Mapbox enabled: {bool(MAPBOX_ACCESS_TOKEN)}")
    if MAPBOX_ACCESS_TOKEN:
        print(f"Mapbox token: {'*' * len(MAPBOX_ACCESS_TOKEN)}")
    print(f"Confidence threshold: {CONFIDENCE_THRESHOLD}")
    print(f"Image size: {IMAGE_SIZE}")
    print(f"API version: {API_VERSION}")
    print("="*50)

    app.run(host='0.0.0.0', port=5000, debug=False)

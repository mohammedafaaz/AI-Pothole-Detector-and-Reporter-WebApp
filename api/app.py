# final
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
import base64
import io
import time
from collections import defaultdict
import logging
try:
    from email_service import EmailService
    print("Email service module imported successfully")
except ImportError as e:
    print(f"Failed to import email service: {e}")
    EmailService = None
import google.generativeai as genai

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
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 3600

# Simple cache for external API calls (in-memory)
external_api_cache = {}
EXTERNAL_API_CACHE_TTL = 300  # seconds

# Initialize Flask app
app = Flask(__name__, static_url_path='/static')

# Enable CORS for React frontend
CORS(app, origins=['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000', 'http://localhost:5173', 
                  'https://*.onrender.com', 'https://*.vercel.app'])

# Add security headers
@app.after_request
def add_security_headers(response):
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
    'POTHOLE_MODEL_PATH': os.getenv('POTHOLE_MODEL_PATH', 'best.pt'),
    'GARBAGE_MODEL_PATH': os.getenv('GARBAGE_MODEL_PATH', 'best2.pt'),
    'ANIMAL_MODEL_PATH': os.getenv('ANIMAL_MODEL_PATH', 'yolov8n/data.pkl'),
    'CONFIDENCE_THRESHOLD': float(os.getenv('CONFIDENCE_THRESHOLD', 0.25)),
    'IMAGE_SIZE': int(os.getenv('IMAGE_SIZE', 640)),
    'MAPBOX_ACCESS_TOKEN': os.getenv('MAPBOX_ACCESS_TOKEN', ''),
    'API_KEY': os.getenv('API_KEY', None),
    'OPENWEATHER_API_KEY': os.getenv('OPENWEATHER_API_KEY', 'bd1fb686e8906028fa3b5af4b6514a39'),
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
    'EMAIL_USER': os.getenv('EMAIL_USER', ''),
    'EMAIL_PASSWORD': os.getenv('EMAIL_PASSWORD', ''),
    'SMTP_SERVER': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'SMTP_PORT': int(os.getenv('SMTP_PORT', 587)),
    'ADMIN_EMAIL': os.getenv('ADMIN_EMAIL', '')
}

# Initialize Gemini AI
gemini_enabled = False
gemini_model = None

print("🔍 Gemini API Initialization:")
print(f"   API Key Present: {'Yes' if config['GEMINI_API_KEY'] else 'No'}")

if config['GEMINI_API_KEY']:
    try:
        print("🔧 Configuring Gemini API...")
        genai.configure(api_key=config['GEMINI_API_KEY'])
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Test the API
        print("🧪 Testing Gemini API connection...")
        test_response = gemini_model.generate_content("Respond with: API Working")
        if test_response and test_response.text:
            print(f"✅ Gemini API test successful: {test_response.text.strip()}")
            gemini_enabled = True
        else:
            print("⚠️ Gemini API test returned empty response")
            
    except Exception as e:
        print(f"❌ Gemini AI initialization failed: {e}")
        gemini_enabled = False
else:
    print("⚠️ Gemini API key not provided")

print(f"Gemini AI enabled: {gemini_enabled}")

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
    print(f"Email user: {config['EMAIL_USER']}")
else:
    print("Email configuration missing:")
    print(f"  EMAIL_USER: {'Present' if config['EMAIL_USER'] else 'Missing'}")
    print(f"  EMAIL_PASSWORD: {'Present' if config['EMAIL_PASSWORD'] else 'Missing'}")

# Validate configuration
def validate_config():
    errors = []
    if not config['POTHOLE_MODEL_PATH']:
        errors.append("POTHOLE_MODEL_PATH is required")
    elif not os.path.exists(config['POTHOLE_MODEL_PATH']):
        errors.append(f"Pothole model file not found: {config['POTHOLE_MODEL_PATH']}")
    
    if not config['GARBAGE_MODEL_PATH']:
        errors.append("GARBAGE_MODEL_PATH is required")
    elif not os.path.exists(config['GARBAGE_MODEL_PATH']):
        errors.append(f"Garbage model file not found: {config['GARBAGE_MODEL_PATH']}")
    
    if not config['ANIMAL_MODEL_PATH']:
        errors.append("ANIMAL_MODEL_PATH is required")
    elif not os.path.exists(config['ANIMAL_MODEL_PATH']):
        errors.append(f"Animal model file not found: {config['ANIMAL_MODEL_PATH']}")
    
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
POTHOLE_MODEL_PATH = config['POTHOLE_MODEL_PATH']
GARBAGE_MODEL_PATH = config['GARBAGE_MODEL_PATH']
ANIMAL_MODEL_PATH = config['ANIMAL_MODEL_PATH']
CONFIDENCE_THRESHOLD = config['CONFIDENCE_THRESHOLD']
IMAGE_SIZE = config['IMAGE_SIZE']
MAPBOX_ACCESS_TOKEN = config['MAPBOX_ACCESS_TOKEN']

# Folder setup
UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Load YOLO models
try:
    print(f"\nLoading pothole model from: {POTHOLE_MODEL_PATH}")
    pothole_model = YOLO(POTHOLE_MODEL_PATH)
    print("Pothole model loaded successfully")
    print(f"Pothole model classes: {list(pothole_model.names.values())}")
    
    print(f"\nLoading garbage model from: {GARBAGE_MODEL_PATH}")
    garbage_model = YOLO(GARBAGE_MODEL_PATH)
    print("Garbage model loaded successfully")
    print(f"Garbage model classes: {list(garbage_model.names.values())}")
    
    print(f"\nLoading animal model from: {ANIMAL_MODEL_PATH}")
    animal_model = YOLO(ANIMAL_MODEL_PATH)
    print("Animal model loaded successfully")
except Exception as e:
    print(f"Error loading models: {str(e)}")
    traceback.print_exc()
    sys.exit(1)

# Rate limiting function
def check_rate_limit(client_ip):
    current_time = time.time()
    request_counts[client_ip] = [
        req_time for req_time in request_counts[client_ip]
        if current_time - req_time < RATE_LIMIT_WINDOW
    ]
    
    if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
        return False
    
    request_counts[client_ip].append(current_time)
    return True

# API Authentication decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
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


def get_cached_external(url):
    now = time.time()
    entry = external_api_cache.get(url)
    if entry and now - entry['time'] < EXTERNAL_API_CACHE_TTL:
        return entry['data']
    return None


def set_cached_external(url, data):
    external_api_cache[url] = {'time': time.time(), 'data': data}

# Helper function to process detection results
def process_detection_results(results, image_width, image_height, input_path, model_used):
    detections = []
    image_diag = math.sqrt(image_width**2 + image_height**2)
    
    for r in results:
        for box in r.boxes:
            if model_used == 'pothole':
                cls = pothole_model.names[int(box.cls)]
            elif model_used == 'garbage':
                cls = garbage_model.names[int(box.cls)]
            else:
                cls = (animal_model.names or {0: 'animal'}).get(int(box.cls), 'animal')
            conf = float(box.conf)
            
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            width, height = x2 - x1, y2 - y1
            box_diag = math.sqrt(width**2 + height**2)
            relative_diag = box_diag / image_diag
            
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

@app.route(f'{API_PREFIX}/health', methods=['GET'])
def api_health():
    return jsonify(create_api_response(
        success=True,
        data={
            'status': 'healthy',
            'pothole_model_loaded': pothole_model is not None,
            'garbage_model_loaded': garbage_model is not None,
            'animal_model_loaded': animal_model is not None,
            'gemini_enabled': gemini_enabled,
            'version': API_VERSION,
            'endpoints': [
                f'{API_PREFIX}/health',
                f'{API_PREFIX}/detect',
                f'{API_PREFIX}/generate-description'
            ]
        },
        message='Dual Detection API is running'
    ))

@app.route(f'{API_PREFIX}/pothole-predictions', methods=['GET'])
@require_api_key
def api_pothole_predictions():
    """Return area-wise pothole risk predictions for government portal.

    Query parameters:
      - areas: optional comma-separated list of area identifiers (we use grouped report center coords)
    """
    try:
        # Basic access control: only allow gov users if API_KEY is set (frontend also checks isGovUser)
        # Aggregate reports into areas using existing data file `data2.yaml` or in-memory reports
        # For simplicity, use grouped reports derived from stored reports in a simple JSON file if exists

        # Load reports from a local store (frontend persists reports in store; server has no DB - use a file if present)
        reports_file = 'reports.json'
        all_reports = []
        if os.path.exists(reports_file):
            try:
                with open(reports_file, 'r', encoding='utf-8') as f:
                    all_reports = json.load(f)
            except Exception:
                all_reports = []

        # If no file exists, attempt to read from a minimal in-memory dataset if available
        # For now, group reports by proximity using the same grouping logic as frontend
        grouped = []
        if all_reports:
            from math import radians, sin, cos, sqrt, atan2

            def distance(lat1, lon1, lat2, lon2):
                R = 6371e3
                phi1 = radians(lat1)
                phi2 = radians(lat2)
                dphi = radians(lat2 - lat1)
                dlambda = radians(lon2 - lon1)
                a = sin(dphi/2) * sin(dphi/2) + cos(phi1) * cos(phi2) * sin(dlambda/2) * sin(dlambda/2)
                c = 2 * atan2(sqrt(a), sqrt(1-a))
                return R * c

            processed = set()
            for r in all_reports:
                if r.get('id') in processed:
                    continue
                nearby = [o for o in all_reports if o.get('id') not in processed and o.get('id') != r.get('id') and distance(r['location']['lat'], r['location']['lng'], o['location']['lat'], o['location']['lng']) <= 50]
                group = [r] + nearby
                for g in group:
                    processed.add(g.get('id'))

                grouped.append({
                    'id': f"group-{r.get('id')}",
                    'location': r['location'],
                    'reports': group
                })

        # For each grouped area, call OpenWeather to fetch weather forecast and compute score
        results = []
        openweather_key = config.get('OPENWEATHER_API_KEY')
        if not openweather_key:
            return jsonify(create_api_response(success=False, error='OpenWeather API key not configured', code='NO_OPENWEATHER')) , 500

        for area in grouped:
            lat = area['location']['lat']
            lon = area['location']['lng']
            # Build API URL for One Call (current + forecast)
            url = f"https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&exclude=minutely&units=metric&appid={openweather_key}"

            cached = get_cached_external(url)
            if cached is not None:
                weather = cached
            else:
                try:
                    resp = requests.get(url, timeout=8)
                    weather = resp.json()
                    set_cached_external(url, weather)
                except Exception as e:
                    weather = None

            # Compute weather risk score
            weather_score = 0.0
            contributing = []
            if weather:
                # Evaluate rainfall (next 48 hours + daily rainfall)
                # Check hourly rain and daily pop
                hourly = weather.get('hourly', [])[:48]
                daily = weather.get('daily', [])[:7]

                # Factor 1: recent heavy rainfall events
                rain_hours = sum(1 for h in hourly if h.get('rain', {}).get('1h', 0) > 2.5)
                if rain_hours > 0:
                    weather_score += min(30, rain_hours * 5)
                    contributing.append(f"Heavy rain hours: {rain_hours}")

                # Factor 2: high precipitation probability in daily forecast
                high_pop_days = sum(1 for d in daily if (d.get('pop', 0) or 0) >= 0.6)
                weather_score += min(30, high_pop_days * 6)
                if high_pop_days:
                    contributing.append(f"High precipitation days: {high_pop_days}")

                # Factor 3: freeze-thaw potential (large temp swings)
                temp_swings = 0
                for d in daily:
                    temp = d.get('temp', {})
                    if temp:
                        if abs(temp.get('max', 0) - temp.get('min', 0)) > 10:
                            temp_swings += 1
                weather_score += min(20, temp_swings * 4)
                if temp_swings:
                    contributing.append(f"Temperature swings: {temp_swings} days")

                # Factor 4: storm alerts (weather alerts)
                alerts = weather.get('alerts', [])
                if alerts:
                    weather_score += 20
                    contributing.append(f"Alerts: {len(alerts)}")

            # Compute report-frequency risk
            recent_window_seconds = 7 * 24 * 3600
            now = time.time()
            recent_reports = [rep for rep in area['reports'] if (now - (datetime.fromisoformat(rep.get('createdAt')).timestamp() if rep.get('createdAt') else now)) <= recent_window_seconds]
            report_count = len(recent_reports)
            # scale: 0 reports -> 0, 1-3 -> 10-30, 4-7 -> 35-60, 8+ -> 70-100 (cap)
            if report_count == 0:
                report_score = 0
            elif report_count <= 3:
                report_score = 10 + (report_count - 1) * 10
            elif report_count <= 7:
                report_score = 35 + (report_count - 4) * 8
            else:
                report_score = 70 + min(30, (report_count - 8) * 2)

            # Combine scores: weighted average (weather 0.6, reports 0.4)
            final_score = round((weather_score * 0.6) + (report_score * 0.4), 2)

            # Determine risk level
            if final_score >= 80:
                level = 'Critical'
            elif final_score >= 60:
                level = 'High'
            elif final_score >= 30:
                level = 'Medium'
            else:
                level = 'Low'

            results.append({
                'areaId': area['id'],
                'center': area['location'],
                'reportCount': len(area['reports']),
                'recentReportCount': report_count,
                'weatherScore': round(weather_score,2),
                'reportScore': round(report_score,2),
                'finalScore': final_score,
                'level': level,
                'contributingFactors': contributing,
                'weatherData': weather
            })

        return jsonify(create_api_response(success=True, data={'predictions': results}))
    except Exception as e:
        logger.error(f"Error in pothole predictions: {e}")
        return jsonify(create_api_response(success=False, error=str(e), code='PREDICTION_ERROR')), 500

@app.route(f'{API_PREFIX}/detect', methods=['POST'])
@require_api_key
def api_detect():
    try:
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
        
        # Get detection type from request
        detection_type = request.form.get('detection_type', 'pothole').lower()
        if detection_type not in ['pothole', 'garbage', 'stray_animals']:
            return jsonify(create_api_response(
                success=False,
                error='Invalid detection type. Must be "pothole", "garbage", or "stray_animals"',
                code='INVALID_DETECTION_TYPE'
            )), 400
        
        # Save uploaded image
        filename = secure_filename(f"api_detection_{detection_type}_{uuid.uuid4().hex}.jpg")
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(input_path)
        
        # Process image
        img = PILImage.open(input_path)
        image_width, image_height = img.size
        
        # Select appropriate model and run detection
        if detection_type == 'pothole':
            results = pothole_model(input_path, conf=CONFIDENCE_THRESHOLD, imgsz=IMAGE_SIZE)
            detections = process_detection_results(results, image_width, image_height, input_path, detection_type)
        elif detection_type == 'garbage':
            garbage_conf = max(0.15, CONFIDENCE_THRESHOLD * 0.6)
            results = garbage_model(input_path, conf=garbage_conf, imgsz=IMAGE_SIZE)
            detections = process_detection_results(results, image_width, image_height, input_path, detection_type)
        else:  # stray_animals
            results = animal_model(input_path, conf=CONFIDENCE_THRESHOLD, imgsz=IMAGE_SIZE)
            detections = process_detection_results(results, image_width, image_height, input_path, 'stray_animals')
        
        # Save annotated image if detections found
        annotated_image_url = None
        if len(detections) > 0:
            try:
                annotated_filename = f"annotated_{detection_type}_detection_{uuid.uuid4().hex}.jpg"
                annotated_path = os.path.join(OUTPUT_FOLDER, annotated_filename)
                annotated_results = results[0].plot()
                cv2.imwrite(annotated_path, annotated_results)
                annotated_image_url = f"/static/outputs/{annotated_filename}"
                logger.info(f"Annotated image saved: {annotated_path}")
            except Exception as e:
                logger.error(f"Failed to save annotated image: {e}")
        
        # Filter detections for relevant classes
        filtered_detections = []
        for detection in detections:
            if detection_type == 'pothole':
                if 'pothole' in detection['class'].lower():
                    filtered_detections.append(detection)
            elif detection_type == 'stray_animals':
                if detection['confidence'] >= CONFIDENCE_THRESHOLD:
                    detection_copy = detection.copy()
                    detection_copy['class'] = 'animal'
                    detection_copy['original_class'] = detection['class']
                    filtered_detections.append(detection_copy)
            else:  # garbage
                class_name = detection['class'].lower()
                if detection['confidence'] >= max(0.15, CONFIDENCE_THRESHOLD * 0.6):
                    detection_copy = detection.copy()
                    detection_copy['class'] = 'garbage'
                    detection_copy['original_class'] = detection['class']
                    filtered_detections.append(detection_copy)
        
        # Prepare response data
        response_data = {
            'detections': filtered_detections,
            'detection_count': len(filtered_detections),
            'detection_type': detection_type,
            'annotated_image_url': annotated_image_url,
            'image_info': {
                'width': image_width,
                'height': image_height,
                'filename': filename
            }
        }
        
        # Clean up file
        def cleanup_file(file_path):
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except OSError:
                pass
        
        import threading
        cleanup_thread = threading.Timer(5.0, cleanup_file, args=[input_path])
        cleanup_thread.start()
        
        detection_name = detection_type.replace('_', ' ').title()
        if len(filtered_detections) == 0:
            message = f'No {detection_name.lower()} detected.'
        else:
            message = f'Detection completed. Found {len(filtered_detections)} {detection_name.lower()}(s).'
        
        return jsonify(create_api_response(
            success=True,
            data=response_data,
            message=message
        ))
    
    except Exception as e:
        return jsonify(create_api_response(
            success=False,
            error=str(e),
            code='DETECTION_ERROR'
        )), 500

@app.route(f'{API_PREFIX}/generate-description', methods=['POST'])
def generate_description():
    try:
        print("🔍 Description request received")
        print(f"   Gemini Enabled: {gemini_enabled}")
        
        if not gemini_enabled:
            return jsonify({
                'success': False,
                'error': 'Gemini AI is not available. Please check API key configuration.',
                'error_type': 'service_unavailable'
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
        except (json.JSONDecodeError, TypeError):
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
        
        print("🤖 Starting Gemini description generation...")
        
        try:
            # Generate description using Gemini
            response = gemini_model.generate_content([prompt, image])
            
            if response and response.text:
                response_text = response.text.strip()
                print(f"✅ Gemini response successful (length: {len(response_text)})")
                return jsonify({
                    'success': True,
                    'description': response_text,
                    'generated_at': datetime.now().isoformat(),
                    'model_used': 'gemini-1.5-flash'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Empty response from Gemini AI',
                    'error_type': 'empty_response'
                }), 500
        
        except Exception as gemini_error:
            error_message = str(gemini_error).lower()
            
            if 'quota' in error_message or 'limit' in error_message:
                return jsonify({
                    'success': False,
                    'error': 'Daily AI quota exceeded. Please try again tomorrow.',
                    'error_type': 'quota_exceeded'
                }), 429
            elif 'timeout' in error_message:
                return jsonify({
                    'success': False,
                    'error': 'AI description generation timed out. Please try again.',
                    'error_type': 'timeout'
                }), 408
            else:
                return jsonify({
                    'success': False,
                    'error': f'AI description generation failed: {str(gemini_error)}',
                    'error_type': 'generation_failed'
                }), 500
    
    except Exception as e:
        print(f"Error generating description: {e}")
        return jsonify({
            'success': False,
            'error': f'Failed to generate description: {str(e)}'
        }), 500

@app.route(f'{API_PREFIX}/send-report-email', methods=['POST'])
def send_report_email():
    """Send email notification for pothole or garbage reports"""
    try:
        logger.info("Email endpoint called")
        logger.info(f"Email enabled: {email_enabled}")
        
        if not email_enabled:
            logger.error("Email service not configured")
            return jsonify({
                'success': False,
                'error': 'Email service not configured'
            }), 503
        
        data = request.get_json()
        if not data:
            logger.error("No data provided to email endpoint")
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        logger.info(f"Email request data keys: {list(data.keys())}")
        
        required_fields = ['user_email', 'user_name', 'detections_data', 'location_data', 'images_data', 'report_type']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        logger.info(f"Sending email for user: {data['user_email']}")
        
        # Initialize email service
        try:
            email_service = EmailService()
            logger.info("Email service initialized successfully")
        except Exception as init_error:
            logger.error(f"Failed to initialize email service: {init_error}")
            return jsonify({
                'success': False,
                'error': f'Email service initialization failed: {str(init_error)}'
            }), 500
        
        # Send report email
        success, error = email_service.send_report_email(
            user_email=data['user_email'],
            user_name=data['user_name'],
            detections_data=data['detections_data'],
            location_data=data['location_data'],
            images_data=data['images_data'],
            report_type=data.get('report_type', 'pothole')
        )
        
        logger.info(f"Email send result - Success: {success}, Error: {error}")
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Report email sent successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': error or 'Failed to send email'
            }), 500
    
    except Exception as e:
        logger.error(f"Error in send_report_email: {e}")
        logger.error(f"Exception traceback: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("\n" + "="*50)
    print("Starting Dual Detection System with Gemini AI")
    print("="*50)
    print(f"Pothole model path: {POTHOLE_MODEL_PATH}")
    print(f"Garbage model path: {GARBAGE_MODEL_PATH}")
    print(f"Animal model path: {ANIMAL_MODEL_PATH}")
    print(f"Gemini AI enabled: {gemini_enabled}")
    print(f"API version: {API_VERSION}")
    print("="*50)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
# 🚧 Pothole Detection System - Complete Setup Guide

## Overview

This system integrates a React-based pothole reporting app with a Flask API powered by YOLO machine learning model for real-time pothole detection.

## 📁 Project Structure

```
project/
├── api/                    # Flask API with YOLO model
│   ├── app.py             # Main Flask application
│   ├── best.pt            # YOLO model file
│   ├── data.yaml          # Model configuration
│   ├── requirements.txt   # Python dependencies
│   ├── .env               # Environment configuration
│   ├── static/            # Static files (uploads/outputs)
│   └── templates/         # HTML templates
├── src/                   # React application
│   ├── components/        # React components
│   ├── hooks/             # Custom React hooks
│   ├── services/          # API services
│   └── utils/             # Utility functions
├── start-api.bat/.sh      # API startup scripts
├── start-both.bat/.sh     # Start both API and React
└── package.json           # React dependencies
```

## 🚀 Quick Start

### Option 1: Start Everything (Recommended)

**Windows:**
```bash
# Double-click or run:
start-both.bat
```

**Linux/Mac:**
```bash
chmod +x start-both.sh
./start-both.sh
```

### Option 2: Start Manually

**1. Start Flask API:**
```bash
# Windows
start-api.bat

# Linux/Mac
./start-api.sh
```

**2. Start React App:**
```bash
npm run dev
```

## 🔧 Manual Setup (If needed)

### 1. Flask API Setup

```bash
cd api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start API
python app.py
```

### 2. React App Setup

```bash
# Install dependencies (if not already done)
npm install

# Start development server
npm run dev
```

## 🌐 Access Points

- **React App**: http://localhost:3000 (or http://localhost:5173)
- **Flask API**: http://localhost:5000
- **API Health Check**: http://localhost:5000/api/v1/health
- **API Documentation**: http://localhost:5000 (web interface)

## 🧪 Testing the Integration

1. **Start both applications** using the startup scripts
2. **Open React app** in your browser
3. **Click the test tube icon (🧪)** in the home page to test API connectivity
4. **Click "Report"** to test the full pothole detection flow:
   - Open camera
   - Capture image
   - AI processes image
   - Submit report
   - View on map with AI annotations

## ⚙️ Configuration

### Environment Variables (.env file in api/ directory)

```env
# Model Configuration
MODEL_PATH=best.pt
CONFIDENCE_THRESHOLD=0.25
IMAGE_SIZE=640

# Email Configuration (optional)
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# API Security (optional)
API_KEY=your-secret-api-key

# Mapbox (optional - for location features)
MAPBOX_ACCESS_TOKEN=your-mapbox-token
```

### Email Setup (Optional)

To enable email notifications:
1. Use Gmail with App Password (recommended)
2. Set `EMAIL_USER` and `EMAIL_PASSWORD` in `.env`
3. Enable 2FA and create App Password in Gmail settings

## 🔍 Features

### ✅ Working Features

- **Real-time Pothole Detection**: YOLO model processes images
- **React Integration**: Seamless UI with camera capture
- **Annotated Images**: AI-highlighted potholes displayed on map
- **Fallback System**: Works even if API is offline
- **Email Notifications**: Optional email alerts with detection results
- **Batch Processing**: Multiple image processing support
- **Health Monitoring**: API status checking
- **Location Support**: GPS coordinates with detections

### 🎯 User Flow

1. **User clicks "Report"** → Opens camera interface
2. **Captures photo** → Image sent to Flask API
3. **YOLO model processes** → Detects potholes and creates annotated image
4. **Results returned** → Shows detection confidence and severity
5. **User adds description** → Submits complete report
6. **Report saved** → Appears on map with AI-annotated image
7. **Optional email** → Sends notification with results

## 🛠️ Troubleshooting

### Common Issues

**1. API Connection Failed**
- Ensure Flask API is running on port 5000
- Check console for CORS errors
- Verify `best.pt` model file exists in `api/` directory

**2. Model Loading Error**
- Ensure `best.pt` is in the correct location
- Check Python dependencies are installed
- Verify YOLO model compatibility

**3. Images Not Loading**
- Check Flask static file serving
- Verify annotated image URLs are correct
- Ensure proper file permissions

**4. Email Not Working**
- Check email configuration in `.env`
- Use Gmail App Password (not regular password)
- Verify SMTP settings

### Debug Tools

- **Test Button (🧪)**: Tests API connectivity
- **Browser Console**: Shows detailed error messages
- **Flask Logs**: Check terminal running Flask API
- **Network Tab**: Inspect API requests/responses

## 📊 API Endpoints

- `GET /api/v1/health` - Health check
- `POST /api/v1/detect` - Single image detection
- `POST /api/v1/detect/batch` - Batch image processing
- `GET /api/v1/system/info` - System information

## 🔒 Security

- Optional API key authentication
- CORS configured for React development
- File upload validation
- Secure email handling

## 📈 Performance

- Synchronous image processing
- Automatic cleanup of temporary files
- Configurable confidence thresholds
- Optimized image sizes

## 🚀 Production Deployment

For production deployment:
1. Set `FLASK_ENV=production` in `.env`
2. Use proper web server (nginx + gunicorn)
3. Configure proper CORS origins
4. Set up SSL certificates
5. Use environment-specific configurations

## 📞 Support

If you encounter issues:
1. Check the setup guide steps
2. Verify all dependencies are installed
3. Test API connectivity using the test button
4. Check browser console and Flask logs
5. Ensure model file (`best.pt`) is accessible

The system is now ready for pothole detection with real AI-powered analysis!

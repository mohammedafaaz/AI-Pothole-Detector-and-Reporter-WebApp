#!/usr/bin/env python3
"""
Test script to verify email functionality with logo and location details
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the email function from app.py
from app import send_email_with_results

def test_email_with_logo_and_location():
    """Test email sending with logo and location data"""
    
    # Test email address
    test_email = "mohammedafaaz433@gmail.com"
    
    # Mock detection data
    test_detections = [
        {
            'class': 'pothole',
            'confidence': 0.856,
            'severity': 'High',
            'relative_size': 0.15
        },
        {
            'class': 'pothole', 
            'confidence': 0.723,
            'severity': 'Medium',
            'relative_size': 0.08
        }
    ]
    
    # Mock location data (New York City coordinates)
    test_location = {
        'latitude': 40.7128,
        'longitude': -74.0060,
        'accuracy': 5
    }
    
    # Mock user info
    test_user_info = {
        'name': 'Test User',
        'email': 'test@example.com'
    }
    
    print("🧪 Testing email with logo and location...")
    print(f"📧 Sending to: {test_email}")
    print(f"📍 Location: {test_location['latitude']}, {test_location['longitude']}")
    print(f"🔍 Detections: {len(test_detections)} potholes found")
    
    # Check if logo exists
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'public', 'logo2.jpg')
    print(f"🖼️ Logo path: {logo_path}")
    print(f"🖼️ Logo exists: {os.path.exists(logo_path)}")
    
    try:
        # Send test email
        success, error = send_email_with_results(
            email=test_email,
            detections=test_detections,
            image_path=None,  # No detection image for this test
            location=test_location,
            user_info=test_user_info
        )
        
        if success:
            print("✅ Test email sent successfully!")
            print("📧 Check your email for:")
            print("   - FixMyPothole.AI logo in header")
            print("   - Detailed location information")
            print("   - Location map (if Mapbox is configured)")
            print("   - GPS coordinates with Google Maps link")
            print("   - Professional email formatting")
        else:
            print(f"❌ Test email failed: {error}")
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_email_with_logo_and_location()

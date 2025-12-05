#!/usr/bin/env python3
"""
Test script to verify the email API endpoint
"""

import requests
import json
import base64

def test_email_api():
    """Test the /api/v1/send-report-email endpoint"""
    
    print("Email API Endpoint Test")
    print("=" * 40)
    
    # API endpoint
    url = "http://localhost:5000/api/v1/send-report-email"
    
    # Test data
    test_data = {
        "user_email": "testuser@example.com",
        "user_name": "Test User",
        "detections_data": [
            [
                {
                    "class": "pothole",
                    "confidence": 0.85,
                    "severity": "High",
                    "bbox": {
                        "x1": 100,
                        "y1": 150,
                        "x2": 200,
                        "y2": 250,
                        "width": 100,
                        "height": 100
                    },
                    "relative_size": 0.3
                }
            ]
        ],
        "location_data": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "address": "Test Location, New York, NY"
        },
        "images_data": [
            "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
        ],
        "report_type": "pothole"
    }
    
    try:
        print("Sending POST request to email API...")
        print(f"URL: {url}")
        print(f"Data: User={test_data['user_name']}, Images={len(test_data['images_data'])}, Type={test_data['report_type']}")
        
        # Send POST request
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            json=test_data,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        # Parse response
        try:
            response_data = response.json()
            print(f"Response JSON: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            print("\n[SUCCESS] Email API test completed successfully!")
            print("Check your email inbox for the test report.")
            return True
        else:
            print(f"\n[FAILED] Email API returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to API server.")
        print("Make sure the Flask API server is running on http://localhost:5000")
        return False
    except requests.exceptions.Timeout:
        print("\n[ERROR] Request timed out.")
        return False
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = test_email_api()
    
    if not success:
        print("\nTroubleshooting:")
        print("1. Make sure the API server is running: python app.py")
        print("2. Check that the server is accessible at http://localhost:5000")
        print("3. Verify email configuration in .env file")
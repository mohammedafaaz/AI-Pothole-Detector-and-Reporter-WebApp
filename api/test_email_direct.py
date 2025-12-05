#!/usr/bin/env python3
"""
Direct test script to verify email sending with application data structure
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add current directory to path to import email_service
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_service import EmailService

# Load environment variables
load_dotenv()

def test_direct_email_send():
    """Test email sending with realistic application data"""
    
    print("Direct Email Send Test")
    print("=" * 40)
    
    try:
        # Initialize email service
        email_service = EmailService()
        print("[OK] Email service initialized successfully")
        
        # Prepare test data similar to what the application sends
        test_data = {
            'user_email': 'testuser@example.com',  # This can be any email
            'user_name': 'Test User',
            'detections_data': [
                [
                    {
                        'class': 'pothole',
                        'confidence': 0.85,
                        'severity': 'High',
                        'bbox': {
                            'x1': 100,
                            'y1': 150,
                            'x2': 200,
                            'y2': 250,
                            'width': 100,
                            'height': 100
                        },
                        'relative_size': 0.3
                    }
                ]
            ],
            'location_data': {
                'latitude': 40.7128,
                'longitude': -74.0060,
                'address': 'Test Location, New York, NY'
            },
            'images_data': [
                'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k='
            ],
            'report_type': 'pothole'
        }
        
        print(f"Test data prepared:")
        print(f"  User: {test_data['user_name']} ({test_data['user_email']})")
        print(f"  Detections: {len(test_data['detections_data'])} images")
        print(f"  Location: {test_data['location_data']['address']}")
        print(f"  Report type: {test_data['report_type']}")
        print()
        
        # Send email
        print("Sending test email...")
        success, error = email_service.send_report_email(
            user_email=test_data['user_email'],
            user_name=test_data['user_name'],
            detections_data=test_data['detections_data'],
            location_data=test_data['location_data'],
            images_data=test_data['images_data'],
            report_type=test_data['report_type']
        )
        
        if success:
            print("[OK] Email sent successfully!")
            print(f"   Email should be delivered to: {os.getenv('ADMIN_EMAIL')}")
            return True
        else:
            print(f"[ERROR] Email sending failed: {error}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_direct_email_send()
    
    if success:
        print("\n[SUCCESS] Direct email test completed successfully!")
        print("Check your email inbox for the test report.")
    else:
        print("\n[FAILED] Direct email test failed!")
        print("Please check the error messages above.")
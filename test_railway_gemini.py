#!/usr/bin/env python3
"""
Test script to verify Gemini API functionality on Railway deployment
"""

import requests
import json
import sys
from PIL import Image
import io

def create_test_image():
    """Create a simple test image"""
    img = Image.new('RGB', (200, 200), color='gray')
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG')
    buffer.seek(0)
    return buffer.getvalue()

def test_railway_gemini(base_url):
    """Test Gemini API functionality on Railway"""
    print(f"🚂 Testing Railway Gemini API Deployment")
    print(f"   Base URL: {base_url}")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1️⃣ Testing Health Endpoint:")
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Health check successful")
            print(f"   📊 Status: {data.get('data', {}).get('status', 'unknown')}")
            print(f"   🤖 Gemini enabled: {data.get('data', {}).get('gemini_enabled', False)}")
            print(f"   🌍 Environment: {data.get('data', {}).get('environment', 'unknown')}")
        else:
            print(f"   ❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Health check error: {e}")
        return False
    
    # Test 2: Gemini Debug
    print("\n2️⃣ Testing Gemini Debug Endpoint:")
    try:
        response = requests.get(f"{base_url}/debug/gemini", timeout=15)
        if response.status_code == 200:
            data = response.json()
            debug_info = data.get('data', {})
            
            print(f"   ✅ Debug endpoint accessible")
            print(f"   🔑 API key configured: {debug_info.get('api_key_configured', False)}")
            print(f"   🤖 Gemini enabled: {debug_info.get('gemini_enabled', False)}")
            print(f"   📱 Model available: {debug_info.get('gemini_model_available', False)}")
            print(f"   🌍 Environment: {debug_info.get('environment', 'unknown')}")
            
            # Check Gemini test
            gemini_test = debug_info.get('gemini_test', {})
            if gemini_test.get('success'):
                print(f"   ✅ Gemini API test: {gemini_test.get('response', 'OK')}")
            else:
                print(f"   ❌ Gemini API test failed: {gemini_test.get('error', 'Unknown error')}")
                return False
                
        else:
            print(f"   ❌ Debug endpoint failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Debug endpoint error: {e}")
        return False
    
    # Test 3: Description Generation
    print("\n3️⃣ Testing Description Generation:")
    try:
        test_image = create_test_image()
        files = {'image': ('test.jpg', test_image, 'image/jpeg')}
        
        response = requests.post(
            f"{base_url}/generate-description", 
            files=files, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                description = data.get('description', '')
                model_used = data.get('model_used', 'unknown')
                print(f"   ✅ Description generated successfully")
                print(f"   🤖 Model used: {model_used}")
                print(f"   📝 Description length: {len(description)} characters")
                print(f"   📄 Preview: {description[:100]}...")
            else:
                print(f"   ❌ Description generation failed: {data.get('error', 'Unknown error')}")
                if 'debug_info' in data:
                    print(f"   🔍 Debug info: {data['debug_info']}")
                return False
        else:
            print(f"   ❌ Description endpoint failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Description generation error: {e}")
        return False
    
    # Test 4: Road Hazard Validation
    print("\n4️⃣ Testing Road Hazard Validation:")
    try:
        test_image = create_test_image()
        files = {'images': ('test.jpg', test_image, 'image/jpeg')}
        
        response = requests.post(
            f"{base_url}/validate-road-hazards", 
            files=files, 
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                validation_data = data.get('data', {})
                hazard_detected = validation_data.get('overall_hazard_detected', False)
                total_images = validation_data.get('total_images', 0)
                print(f"   ✅ Validation completed successfully")
                print(f"   🔍 Hazard detected: {hazard_detected}")
                print(f"   📸 Images processed: {total_images}")
            else:
                print(f"   ❌ Validation failed: {data.get('error', 'Unknown error')}")
                if 'debug_info' in data:
                    print(f"   🔍 Debug info: {data['debug_info']}")
                return False
        else:
            print(f"   ❌ Validation endpoint failed: {response.status_code}")
            print(f"   📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Validation error: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All Gemini API tests passed successfully!")
    print("✅ Railway deployment is working correctly")
    print("🚀 Your application is ready for production use")
    
    return True

def main():
    """Main function"""
    if len(sys.argv) != 2:
        print("Usage: python test_railway_gemini.py <railway_url>")
        print("Example: python test_railway_gemini.py https://your-app.railway.app/api/v1")
        sys.exit(1)
    
    base_url = sys.argv[1].rstrip('/')
    if not base_url.startswith('http'):
        base_url = f"https://{base_url}"
    
    # Ensure it ends with /api/v1
    if not base_url.endswith('/api/v1'):
        if base_url.endswith('/'):
            base_url += 'api/v1'
        else:
            base_url += '/api/v1'
    
    success = test_railway_gemini(base_url)
    
    if not success:
        print("\n" + "=" * 60)
        print("❌ Some tests failed!")
        print("📋 Troubleshooting steps:")
        print("   1. Check GEMINI_API_KEY environment variable in Railway")
        print("   2. Verify API key is valid in Google AI Studio")
        print("   3. Check Railway logs for detailed error messages")
        print("   4. Ensure service is deployed after setting variables")
        print("   5. Review RAILWAY_GEMINI_TROUBLESHOOTING.md for detailed guide")
        sys.exit(1)

if __name__ == "__main__":
    main()

# 🗺️ Location & Map Debug Guide

## 🔍 **Current Issue:**
Email reports are missing:
1. Location coordinates (showing N/A, N/A)
2. Location map image (not appearing)

## 🛠️ **Debugging Steps:**

### **Step 1: Test Location & Map Configuration**
```bash
cd project/api
python test_location_map.py
```

This will test:
- ✅ Mapbox token validity
- ✅ Static map generation
- ✅ Location data parsing
- ✅ Generate test map image

### **Step 2: Check Browser Location Permission**
1. **Open browser console** (F12)
2. **Submit a pothole report**
3. **Look for location messages**:
   ```
   Location captured for email: {latitude: 40.7128, longitude: -74.0060}
   ```
4. **Check for location errors**:
   ```
   Could not get location for detection: GeolocationPositionError
   ```

### **Step 3: Check Flask API Debug Logs**
When you submit a report, look for these messages:

#### **Location Debug:**
```
Location debug - latitude: 40.7128, longitude: -74.0060
Location parsed successfully: {'latitude': 40.7128, 'longitude': -74.0060}
```

#### **Map Generation Debug:**
```
Map generation debug - location: {'latitude': 40.7128, 'longitude': -74.0060}, MAPBOX_ACCESS_TOKEN: True
Generating map for coordinates: 40.7128, -74.0060
Map generation result: /path/to/map.png
```

#### **Email Debug:**
```
Email debug - send_email: True, email: mohammedafaaz433@gmail.com, detections_count: 2, email_enabled: True
Sending admin email to: mohammedafaaz433@gmail.com
Email successfully sent to mohammedafaaz433@gmail.com
```

### **Step 4: Verify Mapbox Configuration**
Check Flask startup logs for:
```
Mapbox enabled: True
Mapbox token: pk.eyJ1Ijoic2hhaWtpc2FhcSIsImEiOiJjbHN5cGp0emkwNXY5MmtucmR4Mmw1YnhhIn0.j_GkyRexLOE1wqUgnDleOg
```

## 🔧 **What I Added for Debugging:**

### **1. Location Capture Debug**
```typescript
// In ReportForm.tsx
console.log('Location captured for email:', locationData);
```

### **2. Flask API Location Debug**
```python
# In app.py
print(f"Location debug - latitude: {latitude}, longitude: {longitude}")
print(f"Location parsed successfully: {location}")
```

### **3. Map Generation Debug**
```python
# In app.py
print(f"Map generation debug - location: {location}, MAPBOX_ACCESS_TOKEN: {bool(MAPBOX_ACCESS_TOKEN)}")
print(f"Generating map for coordinates: {location['latitude']}, {location['longitude']}")
print(f"Map generation result: {map_path}")
```

### **4. Startup Configuration Debug**
```python
# In app.py
print(f"Mapbox enabled: {bool(MAPBOX_ACCESS_TOKEN)}")
if MAPBOX_ACCESS_TOKEN:
    print(f"Mapbox token: {'*' * len(MAPBOX_ACCESS_TOKEN)}")
```

## 🚨 **Common Issues & Solutions:**

### **Issue 1: Browser Location Permission**
- **Problem**: User denied location access
- **Solution**: Enable location permission in browser settings
- **Check**: Browser console shows location error

### **Issue 2: Invalid Mapbox Token**
- **Problem**: Mapbox token expired or invalid
- **Solution**: Generate new token from Mapbox dashboard
- **Check**: Run `test_location_map.py` to verify token

### **Issue 3: Location Not Captured**
- **Problem**: `getCurrentLocation()` fails
- **Solution**: Check browser location settings, try on HTTPS
- **Check**: React console shows location capture message

### **Issue 4: Map Generation Fails**
- **Problem**: Mapbox API request fails
- **Solution**: Check internet connection, verify token
- **Check**: Flask logs show map generation error

### **Issue 5: Email HTML Issues**
- **Problem**: Map image not embedded properly
- **Solution**: Check email client HTML support
- **Check**: View email source to see if map is attached

## 🧪 **Testing Checklist:**

### **Browser Side:**
- [ ] Location permission granted
- [ ] Console shows location captured
- [ ] No location errors in console

### **Flask API Side:**
- [ ] Mapbox token loaded at startup
- [ ] Location data received from React
- [ ] Map generation successful
- [ ] Map file exists and attached to email

### **Email Side:**
- [ ] Location coordinates show in email
- [ ] Map image appears in email
- [ ] Both admin and user receive emails

## 🎯 **Expected Email Content:**

### **Location Section:**
```
Location Details
Coordinates: 40.7128, -74.0060
GPS Accuracy: High precision location data
```

### **Map Section:**
```
LMap
[Location map image with colored marker]
```

## 🔍 **Troubleshooting Commands:**

### **Test Mapbox Token:**
```bash
curl "https://api.mapbox.com/geocoding/v5/mapbox.places/test.json?access_token=YOUR_TOKEN"
```

### **Test Location API:**
```bash
curl -X POST http://localhost:5000/api/detect \
  -F "image=@test_image.jpg" \
  -F "latitude=40.7128" \
  -F "longitude=-74.0060" \
  -F "send_email=true" \
  -F "email=test@example.com"
```

## 🎊 **Next Steps:**

1. **Run location/map test script**
2. **Check browser location permission**
3. **Monitor Flask debug logs**
4. **Verify Mapbox token validity**
5. **Test with different locations**

**The debugging information should help identify exactly where the location/map issue is occurring!** 🗺️✅

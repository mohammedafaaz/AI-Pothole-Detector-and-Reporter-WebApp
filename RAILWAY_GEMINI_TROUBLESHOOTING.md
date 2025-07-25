# 🚂 Railway Gemini API Troubleshooting Guide

## 🔍 **Issue**: Gemini API works on localhost but fails on Railway deployment

### **Common Causes & Solutions:**

## 1️⃣ **Environment Variables (Most Common)**

### **Problem**: Gemini API key not properly set in Railway
```bash
# Check if API key is set
curl https://your-railway-app.railway.app/api/v1/debug/gemini
```

### **Solution**: Set environment variables in Railway
1. Go to your Railway project dashboard
2. Click on your service
3. Go to **Variables** tab
4. Add environment variable:
   - **Name**: `GEMINI_API_KEY`
   - **Value**: `your_actual_gemini_api_key_here`
5. **Deploy** the service

### **Verification**:
```bash
# Check health endpoint
curl https://your-railway-app.railway.app/api/v1/health

# Check debug endpoint
curl https://your-railway-app.railway.app/api/v1/debug/gemini
```

## 2️⃣ **Network/Firewall Issues**

### **Problem**: Railway blocking external API calls
- Railway might have network restrictions
- Gemini API endpoints might be blocked

### **Solution**: Check Railway network policies
```python
# Test network connectivity in Railway logs
import requests
try:
    response = requests.get('https://generativelanguage.googleapis.com')
    print(f"Network test: {response.status_code}")
except Exception as e:
    print(f"Network error: {e}")
```

## 3️⃣ **Memory/Resource Limits**

### **Problem**: Railway resource limits affecting Gemini processing
- Image processing requires memory
- Gemini API calls might timeout

### **Solution**: Optimize resource usage
```python
# Add timeout and memory optimization
import gc
import psutil

# Monitor memory usage
print(f"Memory usage: {psutil.virtual_memory().percent}%")

# Cleanup after processing
gc.collect()
```

## 4️⃣ **CORS and Domain Issues**

### **Problem**: Frontend can't reach Railway backend
- CORS not configured for Railway domain
- Frontend still pointing to localhost

### **Solution**: Update CORS and frontend URLs
```python
# In app.py - Update CORS for Railway
CORS(app, origins=[
    "http://localhost:3000",
    "https://your-frontend-domain.vercel.app",
    "https://your-railway-app.railway.app"
])
```

```javascript
// In frontend - Update API base URL
const API_BASE_URL = process.env.NODE_ENV === 'production' 
    ? 'https://your-railway-app.railway.app/api/v1'
    : 'http://localhost:5000/api/v1';
```

## 🔧 **Debugging Steps**

### **Step 1: Check Railway Logs**
```bash
# View Railway logs
railway logs --follow
```

### **Step 2: Test Endpoints**
```bash
# Test health endpoint
curl https://your-railway-app.railway.app/api/v1/health

# Test Gemini debug endpoint
curl https://your-railway-app.railway.app/api/v1/debug/gemini

# Test description generation
curl -X POST https://your-railway-app.railway.app/api/v1/generate-description \
  -F "image=@test_image.jpg"
```

### **Step 3: Check Environment Variables**
```bash
# In Railway dashboard, verify:
✅ GEMINI_API_KEY is set
✅ API_KEY is set (if using API authentication)
✅ No extra spaces or quotes in values
✅ Variables are deployed (not just saved)
```

### **Step 4: Monitor Resource Usage**
```bash
# Check Railway metrics:
✅ Memory usage < 80%
✅ CPU usage reasonable
✅ No timeout errors
✅ Network connectivity working
```

## 🚀 **Railway Deployment Checklist**

### **Before Deployment:**
- [ ] Gemini API key obtained from Google AI Studio
- [ ] API key tested locally
- [ ] All environment variables documented
- [ ] CORS configured for production domain
- [ ] Frontend updated with production API URL

### **During Deployment:**
- [ ] Environment variables set in Railway
- [ ] Service deployed successfully
- [ ] Health endpoint responding
- [ ] Debug endpoint shows Gemini enabled
- [ ] No errors in Railway logs

### **After Deployment:**
- [ ] Test description generation endpoint
- [ ] Test road hazard validation endpoint
- [ ] Verify frontend can reach backend
- [ ] Check all Gemini features working
- [ ] Monitor for any timeout/memory issues

## 🔍 **Diagnostic Commands**

### **Check API Status:**
```bash
# Health check
curl https://your-app.railway.app/api/v1/health

# Expected response:
{
  "success": true,
  "data": {
    "status": "healthy",
    "gemini_enabled": true,
    "environment": "railway"
  }
}
```

### **Check Gemini Configuration:**
```bash
# Gemini debug
curl https://your-app.railway.app/api/v1/debug/gemini

# Expected response:
{
  "success": true,
  "data": {
    "gemini_enabled": true,
    "api_key_configured": true,
    "gemini_test": {
      "success": true,
      "response": "OK"
    }
  }
}
```

### **Test Description Generation:**
```bash
# Test with image
curl -X POST https://your-app.railway.app/api/v1/generate-description \
  -F "image=@pothole_image.jpg"

# Expected response:
{
  "success": true,
  "description": "**Damage Assessment:**\n...",
  "model_used": "gemini-1.5-flash"
}
```

## ⚠️ **Common Error Messages & Solutions**

### **"Gemini AI service not available"**
- ❌ API key not set in Railway
- ✅ Set GEMINI_API_KEY environment variable

### **"Authentication failed"**
- ❌ Invalid API key
- ✅ Verify API key is correct and active

### **"Network connection issue"**
- ❌ Railway network restrictions
- ✅ Check Railway logs for network errors

### **"Quota exceeded"**
- ❌ Gemini API quota reached
- ✅ Check Google AI Studio quota limits

### **"Timeout"**
- ❌ Railway resource limits
- ✅ Optimize image processing or upgrade Railway plan

## 📞 **Support Resources**

- **Railway Documentation**: https://docs.railway.app/
- **Google AI Studio**: https://makersuite.google.com/
- **Gemini API Docs**: https://ai.google.dev/docs
- **Railway Discord**: https://discord.gg/railway

## 🎯 **Quick Fix Checklist**

1. **Set GEMINI_API_KEY in Railway environment variables**
2. **Deploy the service after setting variables**
3. **Check `/api/v1/debug/gemini` endpoint**
4. **Verify Railway logs for errors**
5. **Test with simple image first**
6. **Update frontend to use Railway URL**

**Most issues are resolved by properly setting the GEMINI_API_KEY environment variable in Railway!** 🔑

# 🚀 Deployment Guide

## Architecture Overview
This project consists of two parts that need to be deployed separately:
- **Frontend** (React) → Deploy to Vercel
- **Backend** (Flask API) → Deploy to Railway/Render/Heroku

## 📱 Frontend Deployment (Vercel)

### Step 1: Prepare for Deployment
```bash
# Build the project
npm run build

# Test the build locally
npm run preview
```

### Step 2: Deploy to Vercel
1. Push your code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Import your GitHub repository
4. Configure build settings:
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

### Step 3: Environment Variables
In Vercel dashboard, add environment variable:
- **Name**: `VITE_API_BASE_URL`
- **Value**: `https://your-api-domain.railway.app/api/v1`

## 🐍 Backend Deployment (Railway - Recommended)

### Step 1: Prepare API for Deployment
Create `railway.json` in the `api` folder:
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "python app.py",
    "healthcheckPath": "/api/v1/health"
  }
}
```

### Step 2: Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Create new project
3. Connect GitHub repository
4. Select the `api` folder as root
5. Deploy automatically

### Step 3: Update Frontend
Update your Vercel environment variable with the Railway URL.

## 🔧 Alternative Backend Deployment Options

### Option A: Render
1. Go to [render.com](https://render.com)
2. Create new Web Service
3. Connect GitHub repo
4. Set root directory to `api`
5. Build command: `pip install -r requirements.txt`
6. Start command: `python app.py`

### Option B: Heroku
```bash
# In api folder
echo "web: python app.py" > Procfile
git subtree push --prefix=api heroku main
```

## 📝 Important Notes

1. **Model File Size**: The `best.pt` file might be large. Consider using Git LFS or cloud storage.

2. **CORS Configuration**: Make sure your Flask API allows requests from your Vercel domain.

3. **Environment Variables**: Update API URLs in production.

4. **Static Files**: Ensure the Flask API can serve static files for annotated images.

## 🧪 Testing Deployment

1. Test frontend: Visit your Vercel URL
2. Test API: Visit `https://your-api-domain/api/v1/health`
3. Test integration: Try creating a report with photo

## 🔄 Continuous Deployment

Both Vercel and Railway support automatic deployment from GitHub:
- Push to main branch → Automatic deployment
- Pull requests → Preview deployments

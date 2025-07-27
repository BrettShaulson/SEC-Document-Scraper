# SEC Document Scraper

A simple web application for extracting sections from SEC 10-K, 10-Q, and 8-K filings with **Google Cloud Firestore** storage.

## Features

- Clean React frontend with section selection
- Flask backend using sec-api.io
- Auto-detection of filing type from URL
- Support for all major SEC filing sections
- **📊 Google Cloud Firestore integration** - All scraped data automatically saved
- **🔍 Data viewing** - Query saved filings and sections

## 🚀 Getting Started

### **Prerequisites**
Before running the application, ensure you have:
- **Python 3.7+** installed
- **Node.js 14+** and npm installed
- **Google Cloud CLI** configured
- **Google Cloud Project** with Firestore enabled

### **Step 1: Google Cloud Authentication**
```bash
# Authenticate with Google Cloud (opens browser)
gcloud auth application-default login

# Set your Google Cloud project
gcloud config set project sentiment-analysis-379200
```

### **Step 2: Backend Setup**
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip3 install -r requirements.txt

# Start the Flask server (runs on http://localhost:8080)
python3 app.py
```

### **Step 3: Frontend Setup**
In a **new terminal window**:
```bash
# Navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install

# Start the React development server (opens http://localhost:3000)
npm start
```

### **Step 4: Access the Application**
- **Frontend**: http://localhost:3000 (React development server)
- **Backend API**: http://localhost:8080 (Flask server)
- **Health Check**: http://localhost:8080/healthz

## 🚀 Deployment Options

### **Quick Reference**

| Environment | Script | Purpose |
|-------------|--------|---------|
| **Local Development** | `./start-local.sh` | Run on your laptop/desktop (no sudo required) |
| **Google Cloud** | `./start-servers.sh` | Deploy to Google Cloud Compute Engine |
| **Manual Setup** | Individual commands | Full control over each step |

## 🚀 Google Cloud Compute Engine Deployment

### **Option 1: Automated Deployment (Recommended)**

The easiest way to deploy on Google Cloud Compute Engine:

```bash
# On your Google Cloud Compute Engine instance:
cd ~/sec-scraper/SEC-Document-Scraper

# Run the automated deployment script
./start-servers.sh
```

**What the automated script does:**
- ✅ Installs all dependencies (Python3, Node.js, npm)
- ✅ Sets up Google Cloud authentication check
- ✅ Starts both backend (port 8080) and frontend (port 3000)
- ✅ Creates firewall rules automatically
- ✅ Shows you the URLs to access your app
- ✅ Runs both services in background with logging

## 🏠 Local Development

### **Quick Start for Local Development**

For local development on your laptop/desktop:

```bash
# Navigate to project directory
cd SEC-Document-Scraper

# Run the local development script
./start-local.sh
```

**What the local script does:**
- ✅ Checks dependencies without requiring sudo
- ✅ Stops existing processes gracefully (no password required)
- ✅ Installs dependencies and starts both servers
- ✅ Auto-opens browser to http://localhost:3000
- ✅ Shows local and network IP addresses
- ✅ Provides easy stop commands

### **Manual Local Setup** (Alternative)

If you prefer manual control:

**Terminal 1 (Backend):**
```bash
cd backend
pip3 install -r requirements.txt
python3 app.py
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm install
npm start
```

### **Option 2: Manual Google Cloud Setup**

If you prefer manual control on Google Cloud:

**Terminal 1 (Backend):**
```bash
cd ~/sec-scraper/SEC-Document-Scraper/backend
pip3 install -r requirements.txt
python3 app.py
```

**Terminal 2 (Frontend):**
```bash
cd ~/sec-scraper/SEC-Document-Scraper/frontend
npm install
npm start
```

### **🔥 Firewall Rules (Google Cloud)**

```bash
# Allow frontend access (port 3000)
gcloud compute firewall-rules create allow-frontend-3000 \
    --allow tcp:3000 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow React frontend access" \
    --project=sentiment-analysis-379200

# Allow backend access (port 8080)  
gcloud compute firewall-rules create allow-backend-8080 \
    --allow tcp:8080 \
    --source-ranges 0.0.0.0/0 \
    --description "Allow Flask backend access" \
    --project=sentiment-analysis-379200
```

### **🌐 Access Your Application (Google Cloud)**

Once deployed on Google Cloud, access your app at:
- **Frontend**: `http://[YOUR-EXTERNAL-IP]:3000`
- **Backend API**: `http://[YOUR-EXTERNAL-IP]:8080`
- **Health Check**: `http://[YOUR-EXTERNAL-IP]:8080/healthz`

Get your external IP:
```bash
curl ifconfig.me
```

### **📊 Monitoring & Logs**

```bash
# Check if services are running
ps aux | grep -E "(python3 app.py|react-scripts)"

# View real-time logs
tail -f backend.log    # Backend logs
tail -f frontend.log   # Frontend logs

# Check service status
curl http://localhost:8080/healthz  # Backend health check
curl http://localhost:3000          # Frontend status
```

### **🛑 Stop Services**

**Stop individual services:**
```bash
# Stop backend only
sudo pkill -f "python3 app.py"

# Stop frontend only
sudo pkill -f "react-scripts start"
```

**Stop all services:**
```bash
# Stop both backend and frontend
sudo pkill -f "python3 app.py"
sudo pkill -f "react-scripts start"

# Or if you have the process IDs from the start script:
kill [BACKEND_PID] [FRONTEND_PID]
```

**Clean shutdown:**
```bash
# Kill all related Node.js and Python processes
sudo pkill -f "node.*react-scripts"
sudo pkill -f "python3.*app.py"

# Remove log files (optional)
rm -f backend.log frontend.log
```

## Quick Start

### Local Development

1. **Setup Google Cloud Authentication:**
```bash
gcloud auth application-default login
```

2. **Backend Setup:**
```bash
cd backend
pip3 install -r requirements.txt
python3 app.py
```

3. **Frontend Setup:**
```bash
cd frontend
npm install
npm start
```

The app will be available at `http://localhost:3000`

### Usage

1. Enter a SEC document URL (from sec.gov)
2. Select the sections you want to extract
3. Click "Extract Sections" to scrape the content
4. **Data is automatically saved to Google Cloud Firestore** 💾

## API Endpoints

- `GET /healthz` - Health check with Firestore status
- `GET /sections` - Get available sections by filing type
- `POST /detect-filing-type` - Auto-detect filing type from URL
- `POST /scrape` - Extract selected sections from filing
- `GET /filings` - **NEW!** List saved filings from Firestore
- `GET /filings/<filing_id>/sections/<section_id>` - Get specific section content

## Data Storage

All scraped data is automatically saved to **Google Cloud Firestore** with this structure:

**Filing Documents:**
- Filing ID (unique hash)
- URL, filing type, timestamp
- Section counts and success/failure stats

**Section Documents:**
- Section content and metadata
- Content length and success status
- Linked to parent filing

## Troubleshooting

### **Common Issues:**

**Backend won't start:**
```bash
# Check if port is in use
lsof -i :8080

# Check backend logs
cat backend.log

# Verify dependencies
pip3 list | grep -E "(flask|sec-api|google-cloud)"
```

**Frontend won't start:**
```bash
# Check if port is in use
lsof -i :3000

# Check frontend logs
cat frontend.log

# Clear npm cache
npm cache clean --force
```

**Firestore connection issues:**
```bash
# Check authentication
gcloud auth application-default print-access-token

# Check project configuration
gcloud config get-value project

# Test Firestore access
curl http://localhost:8080/healthz
```

**Google Cloud access issues:**
```bash
# Check external IP
curl ifconfig.me

# Verify firewall rules
gcloud compute firewall-rules list --filter="name~allow-(frontend|backend)"

# Check if services are bound to all interfaces
netstat -tlnp | grep -E ":3000|:8080"
```

## Requirements

- Python 3.7+
- Node.js 14+
- Google Cloud Project with Firestore enabled
- SEC API key (already included for demo)

## Structure

```
├── backend/           # Flask API server
│   ├── app.py        # Main application with Firestore integration
│   └── requirements.txt
├── frontend/         # React web interface
│   ├── src/
│   │   ├── ScraperForm.jsx
│   │   └── ScraperForm.css
│   └── package.json
├── start-servers.sh  # Automated deployment script
└── README.md
```

## Production Deployment

1. Update the API URL in `frontend/src/ScraperForm.jsx`:
```javascript
const API_BASE = 'https://your-backend-domain.com';
```

2. Ensure Google Cloud authentication is configured on your server
3. Deploy both frontend and backend to your hosting platform

## Example Response

```json
{
  "filing_type": "10-K",
  "filing_id": "703e2d880500",
  "firestore_saved": true,
  "summary": {
    "successful_sections": 1,
    "failed_sections": 0,
    "total_sections": 1
  },
  "results": [...]
}
```

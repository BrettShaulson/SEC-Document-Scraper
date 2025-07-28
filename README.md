# SEC Document Scraper

A web application for extracting sections from SEC 10-K, 10-Q, and 8-K filings with **Google Cloud Firestore** storage.

## Features

- 🎯 Clean React frontend with section selection  
- ⚡ Flask backend using sec-api.io for document extraction
- 🤖 Auto-detection of filing type from URL
- 📊 **Google Cloud Firestore integration** - All data automatically saved with session tracking
- 🔍 **Data viewing** - Query saved filings and sections by session
- 📈 **Session isolation** - Each scrape operation gets its own session for accurate tracking

## 🚀 Quick Start

### **Prerequisites**
- **Python 3.7+** and **Node.js 14+** installed
- **Google Cloud CLI** configured with Firestore enabled

### **Access**
#### **Local**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080
- **Health Check**: http://localhost:8080/healthz
#### **On Compute Engine**
- **Frontend**: http://(Compute Engine External IP):3000
- **Backend API**: http://(Compute Engine External IP):8080
- **Health Check**: http://(Compute Engine External IP):8080/healthz

## 🚀 Deployment

### **🖥️ Local Development (Automated)**

Use the automated startup script for local development:

```bash
./start-local.sh
```

**What it does:**
- ✅ Automatically kills any existing processes on ports 3000/8080
- ✅ Starts Flask backend with health check verification
- ✅ Starts React frontend with compilation verification
- ✅ Provides process IDs for easy management
- ✅ Auto-opens browser (macOS)
- ✅ Shows all access URLs and stop commands

**To stop services (run before just in case):**
```bash
# Use the provided process IDs from script output
kill [BACKEND_PID] [FRONTEND_PID]

# Or kill all processes on the ports
kill -9 $(lsof -ti:3000,8080)
```

### **☁️ Google Cloud Compute Engine**

Use the comprehensive cloud deployment script:

```bash
./start-servers.sh
```

**What it does:**
- ✅ **Dependency Management**: Auto-installs Python3, Node.js, npm if missing
- ✅ **Authentication Check**: Verifies Google Cloud authentication status
- ✅ **Port Management**: Handles port conflicts automatically
- ✅ **Service Startup**: Starts both backend and frontend as background processes
- ✅ **Network Configuration**: Gets external/internal IP addresses
- ✅ **Firewall Setup**: Creates Google Cloud firewall rules for ports 3000/8080
- ✅ **Health Verification**: Confirms both services started successfully
- ✅ **Log Management**: Creates separate log files for debugging

**Access URLs (after deployment):**
- **Frontend**: `http://[EXTERNAL_IP]:3000`
- **Backend API**: `http://[EXTERNAL_IP]:8080`
- **Health Check**: `http://[EXTERNAL_IP]:8080/healthz`

**Log Files:**
- Backend logs: `backend.log`
- Frontend logs: `frontend.log`

### **📋 Manual Setup**

If you prefer manual setup or need to troubleshoot:

```bash
# 1. Authenticate with Google Cloud
gcloud auth application-default login
gcloud config set project sentiment-analysis-379200

# 2. Backend Setup
cd backend
pip3 install -r requirements.txt
python3 app.py

# 3. Frontend Setup (new terminal)
cd frontend
npm install
npm start
```

## 📊 Database Structure

**Scrape Session Hierarchy** (solves data consistency issues):
```
filings/{filing_id}/
├── total_unique_sections, total_sessions, latest_session_id
└── scrape_sessions/{session_id}/
    ├── scraped_at, requested_sections, successful_sections
    └── sections/{section_id}/
        ├── content, content_length, success, error
        └── scraped_at, session_id
```

## 🔌 API Endpoints

### **Core Endpoints**
- `GET /healthz` - Health check with Firestore status
- `GET /sections` - Available sections by filing type
- `POST /detect-filing-type` - Auto-detect filing type from URL
- `POST /scrape` - Extract sections (returns `session_id`)

### **New Session-Based Endpoints**
- `GET /filings` - List all filings with session summary
- `GET /filings/{filing_id}/sessions` - All scrape sessions for a filing
- `GET /filings/{filing_id}/sessions/{session_id}/sections` - Sections from specific session
- `GET /filings/{filing_id}/sessions/{session_id}/sections/{section_id}` - Specific section content

### **Legacy Endpoint** (backward compatible)
- `GET /filings/{filing_id}/sections/{section_id}` - Gets section from latest session

## 💡 Usage

1. **Extract Sections:**
   - Enter SEC document URL (from sec.gov)
   - Select sections to extract
   - Click "Extract Sections"
   - Get unique `session_id` for this scrape operation

2. **View Data:**
   - All data automatically saved to Firestore
   - Each scrape gets isolated session
   - Query by filing, session, or specific section

## 🔧 Troubleshooting

### **Port Issues:**
```bash
# Check what's running on ports
lsof -i :8080
lsof -i :3000

# Kill processes using ports
lsof -ti:8080 | xargs kill
lsof -ti:3000 | xargs kill
```

### **Backend Issues:**
```bash
# Check backend logs
cat backend.log

# Verify dependencies
pip3 list | grep -E "(flask|sec-api|google-cloud)"

# Test Firestore connection
curl http://localhost:8080/healthz
```

### **Frontend Issues:**
```bash
# Check frontend logs
cat frontend.log

# Clear npm cache and reinstall
npm cache clean --force
rm -rf node_modules
npm install
```

## 📊 Example Response

```json
{
  "filing_type": "10-K",
  "filing_id": "703e2d880500",
  "session_id": "2025-07-28_16-43-54",
  "firestore_saved": true,
  "summary": {
    "successful_sections": 1,
    "failed_sections": 0,
    "total_sections": 1
  },
  "results": [...]
}

```

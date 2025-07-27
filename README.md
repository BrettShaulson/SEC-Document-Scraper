# SEC Document Scraper

A simple web application for extracting sections from SEC 10-K, 10-Q, and 8-K filings with **Google Cloud Datastore** storage.

## Features

- Clean React frontend with section selection
- Flask backend using sec-api.io
- Auto-detection of filing type from URL
- Support for all major SEC filing sections
- **📊 Google Cloud Datastore integration** - All scraped data automatically saved
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
4. **Data is automatically saved to Google Cloud Datastore** 💾

## API Endpoints

- `GET /healthz` - Health check with Datastore status
- `GET /sections` - Get available sections by filing type
- `POST /detect-filing-type` - Auto-detect filing type from URL
- `POST /scrape` - Extract selected sections from filing
- `GET /filings` - **NEW!** List saved filings from Datastore

## Data Storage

All scraped data is automatically saved to **Google Cloud Datastore** with this structure:

**Filing Entities:**
- Filing ID (unique hash)
- URL, filing type, timestamp
- Section counts and success/failure stats

**Section Entities:**
- Section content and metadata
- Content length and success status
- Linked to parent filing

## Requirements

- Python 3.7+
- Node.js 14+
- Google Cloud Project with Datastore enabled
- SEC API key (already included for demo)

## Structure

```
├── backend/           # Flask API server
│   ├── app.py        # Main application with Datastore integration
│   └── requirements.txt
└── frontend/         # React web interface
    ├── src/
    │   ├── ScraperForm.jsx
    │   └── ScraperForm.css
    └── package.json
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
  "datastore_saved": true,
  "summary": {
    "successful_sections": 1,
    "failed_sections": 0,
    "total_sections": 1
  },
  "results": [...]
}
```

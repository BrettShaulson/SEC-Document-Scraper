# SEC Document Scraper

A simple web application for extracting sections from SEC 10-K, 10-Q, and 8-K filings with **Google Cloud Datastore** storage.

## Features

- Clean React frontend with section selection
- Flask backend using sec-api.io
- Auto-detection of filing type from URL
- Support for all major SEC filing sections
- **📊 Google Cloud Datastore integration** - All scraped data automatically saved
- **🔍 Data viewing** - Query saved filings and sections

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

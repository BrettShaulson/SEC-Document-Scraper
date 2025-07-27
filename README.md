# SEC Document Section Scraper

A comprehensive web application for extracting specific sections from SEC 10-K, 10-Q, and 8-K filings using a React frontend and Flask backend, optimized for Google Cloud Platform deployment.

## Features

### 🎯 Comprehensive Section Support
- **10-K Filings**: All 16 sections (1, 1A, 1B, 1C, 2, 3, 4, 5, 6, 7, 7A, 8, 9, 9A, 9B, 9C, 10, 11, 12, 13, 14, 15)
- **10-Q Filings**: All Part 1 and Part 2 sections
- **8-K Filings**: Complete range of item sections including 1-1 through 9-1

### 🎨 Modern User Interface
- Responsive design that works on all devices
- Professional gradient background and clean card layout
- Intuitive section selection with descriptions
- Real-time filing type detection
- Loading states and comprehensive error handling
- Connection status monitoring

### 🔧 Advanced Features
- Auto-detection of filing type from URL
- Batch section selection (Select All/Clear All)
- Detailed extraction results with content metrics
- Professional styling with smooth animations
- Comprehensive section descriptions to help users understand what each section contains

### ☁️ Google Cloud Integration
- **Google Cloud Datastore**: Secure storage of extracted sections
- **Cloud Run**: Serverless deployment with auto-scaling
- **Compute Engine**: Alternative deployment option
- **Cloud Build**: Automated CI/CD pipeline
- **IAM Integration**: Secure service account management

## Prerequisites

- **Google Cloud Platform Account** with billing enabled
- **gcloud CLI** installed and configured
- **Docker** (for local development)
- **Node.js 14+** (for frontend development)
- **Python 3.8+** (for backend development)
- **SEC API Key** (included in the code)

## Quick Start - Google Cloud Deployment

### 1. Set up Google Cloud Project

```bash
# Set your project ID
export GOOGLE_CLOUD_PROJECT="your-project-id"

# Authenticate with Google Cloud
gcloud auth login
gcloud config set project $GOOGLE_CLOUD_PROJECT
```

### 2. Deploy to Google Cloud

**Option A: Automated Deployment (Recommended)**
```bash
# Make the deployment script executable
chmod +x deploy.sh

# Deploy to Cloud Run (recommended)
./deploy.sh cloud-run

# Or deploy to Compute Engine
./deploy.sh compute-engine

# Or deploy using Cloud Build
./deploy.sh cloud-build
```

**Option B: Manual Deployment**
```bash
# Enable required APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com datastore.googleapis.com

# Deploy backend to Cloud Run
cd backend
gcloud builds submit --tag gcr.io/$GOOGLE_CLOUD_PROJECT/sec-document-scraper
gcloud run deploy sec-document-scraper \
  --image gcr.io/$GOOGLE_CLOUD_PROJECT/sec-document-scraper \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

### 3. Deploy Frontend

The frontend can be deployed to Firebase Hosting or any static hosting service:

```bash
cd frontend
npm install
npm run build

# Deploy to Firebase (if configured)
firebase deploy

# Or serve the build folder on any static hosting service
```

## Local Development Setup

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install Python dependencies:
   ```bash
   pip3 install -r requirements.txt
   ```

3. Set up Google Cloud credentials (optional for local development):
   ```bash
   gcloud auth application-default login
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   ```

4. Run the Flask server:
   ```bash
   python3 app.py
   ```

The backend will start on `http://localhost:8080`

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Set the backend URL (optional):
   ```bash
   export REACT_APP_API_BASE=http://localhost:8080
   ```

4. Start the development server:
   ```bash
   npm start
   ```

The frontend will start on `http://localhost:3000`

## Usage

1. **Enter SEC Filing URL**: Paste the full URL of a SEC EDGAR filing (must be from sec.gov and end with .htm or .txt)

2. **Select Filing Type**: The app will auto-detect the filing type (10-K, 10-Q, or 8-K), or you can manually select

3. **Choose Sections**: Select the specific sections you want to extract. Each section includes a helpful description of its contents

4. **Extract**: Click the extract button to process the selected sections

5. **Review Results**: View detailed results including success/failure status and content metrics. Data is automatically stored in Google Cloud Datastore.

## Architecture

### Backend (Flask)
- **Runtime**: Python 3.11
- **Framework**: Flask with CORS support
- **Storage**: Google Cloud Datastore
- **API Integration**: SEC API for document extraction
- **Deployment**: Docker container on Cloud Run or Compute Engine
- **Monitoring**: Google Cloud Logging and Monitoring

### Frontend (React)
- **Framework**: React 18 with modern hooks
- **HTTP Client**: Axios with timeout handling
- **Styling**: CSS3 with custom properties and responsive design
- **Build Tool**: React Scripts
- **Deployment**: Static hosting (Firebase Hosting recommended)

### Google Cloud Services
- **Cloud Run**: Serverless container platform (recommended)
- **Compute Engine**: Virtual machine option
- **Cloud Datastore**: NoSQL document database
- **Cloud Build**: CI/CD pipeline
- **Container Registry**: Docker image storage
- **IAM**: Identity and access management

## API Endpoints

### Backend Endpoints

- `GET /` - Service information and status
- `GET /sections` - Returns all available sections for each filing type
- `POST /detect-filing-type` - Auto-detects filing type from URL
- `POST /scrape` - Extracts selected sections from filing
- `GET /healthz` - Health check endpoint

### Request/Response Examples

**Scrape Request:**
```json
{
  "filing_url": "https://www.sec.gov/Archives/edgar/data/1318605/000156459021004599/tsla-10k_20201231.htm",
  "sections": ["1", "1A", "7"]
}
```

**Scrape Response:**
```json
{
  "results": {
    "1": {
      "status": "success",
      "message": "Section extracted and stored successfully in Datastore",
      "content_length": 15420
    }
  },
  "summary": {
    "total_sections": 3,
    "successful": 2,
    "failed": 1,
    "successful_sections": ["1", "1A"],
    "failed_sections": ["7"],
    "filing_type": "10-K"
  },
  "datastore_available": true,
  "project_id": "your-project-id"
}
```

## Configuration

### Environment Variables

**Backend:**
- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `PORT`: Server port (default: 8080)
- `FLASK_ENV`: Environment (development/production)

**Frontend:**
- `REACT_APP_API_BASE`: Backend API URL
- `NODE_ENV`: Environment (development/production)

### Google Cloud Configuration

The application uses the following Google Cloud services:

1. **Cloud Datastore**: For storing extracted sections
2. **Cloud Run**: For hosting the backend API
3. **Cloud Build**: For CI/CD pipeline
4. **IAM**: Service account with the following roles:
   - `roles/datastore.user`
   - `roles/logging.logWriter`
   - `roles/monitoring.metricWriter`

## Deployment Options

### Cloud Run (Recommended)
- Serverless and auto-scaling
- Pay-per-use pricing
- Automatic HTTPS
- Easy to deploy and manage

```bash
./deploy.sh cloud-run
```

### Compute Engine
- More control over the environment
- Persistent instances
- Custom machine configurations

```bash
./deploy.sh compute-engine
```

### Cloud Build
- Automated CI/CD pipeline
- Build triggers from Git repositories
- Multi-environment deployments

```bash
./deploy.sh cloud-build
```

## Monitoring and Logging

The application includes comprehensive logging and monitoring:

- **Application Logs**: Structured logging to Google Cloud Logging
- **Health Checks**: Built-in health check endpoints
- **Error Handling**: Comprehensive error handling and reporting
- **Performance Metrics**: Request latency and throughput monitoring

View logs in the Google Cloud Console:
```bash
gcloud logs read "resource.type=cloud_run_revision" --limit=50
```

## Security

- **Service Account**: Dedicated service account with minimal required permissions
- **CORS**: Configurable CORS policies
- **HTTPS**: Automatic HTTPS on Cloud Run
- **Input Validation**: URL validation and sanitization
- **Rate Limiting**: Built-in request throttling

## Cost Optimization

- **Cloud Run**: Scales to zero when not in use
- **Efficient Storage**: Only stores successfully extracted sections
- **Request Batching**: Supports multiple section extraction in single request
- **Connection Pooling**: Efficient database connections

## Troubleshooting

### Common Issues

1. **Datastore Permission Errors**
   ```bash
   gcloud auth application-default login
   gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
     --member="user:your-email@gmail.com" \
     --role="roles/datastore.user"
   ```

2. **Frontend Cannot Connect to Backend**
   - Check the `REACT_APP_API_BASE` environment variable
   - Verify CORS configuration in the backend
   - Ensure the backend service is running

3. **SEC API Rate Limiting**
   - The application includes built-in retry logic
   - Consider implementing additional rate limiting if needed

### Support

For deployment issues:
1. Check Google Cloud Console for error logs
2. Verify IAM permissions
3. Ensure all required APIs are enabled

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with both local and Google Cloud environments
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Disclaimer

This application is for educational and research purposes. Users are responsible for complying with SEC terms of service and any applicable regulations when accessing EDGAR filings.

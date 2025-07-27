#!/bin/bash

# SEC Document Scraper - Google Cloud Deployment Script
# This script deploys the application to Google Cloud Platform

set -e

# Configuration
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"your-project-id"}
SERVICE_NAME="sec-document-scraper"
REGION="us-central1"
SERVICE_ACCOUNT="sec-scraper-service@${PROJECT_ID}.iam.gserviceaccount.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if gcloud is installed and authenticated
check_gcloud() {
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it first."
        exit 1
    fi

    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "No active gcloud authentication found. Please run 'gcloud auth login'"
        exit 1
    fi

    print_success "gcloud CLI is installed and authenticated"
}

# Function to set up the Google Cloud project
setup_project() {
    print_status "Setting up Google Cloud project: $PROJECT_ID"
    
    gcloud config set project $PROJECT_ID
    
    # Enable required APIs
    print_status "Enabling required APIs..."
    gcloud services enable \
        cloudbuild.googleapis.com \
        run.googleapis.com \
        datastore.googleapis.com \
        containerregistry.googleapis.com \
        compute.googleapis.com
    
    print_success "APIs enabled successfully"
}

# Function to create IAM service account
create_service_account() {
    print_status "Creating service account: $SERVICE_ACCOUNT"
    
    # Check if service account already exists
    if gcloud iam service-accounts describe $SERVICE_ACCOUNT &> /dev/null; then
        print_warning "Service account already exists"
    else
        gcloud iam service-accounts create sec-scraper-service \
            --display-name="SEC Document Scraper Service Account" \
            --description="Service account for SEC document scraping application"
        print_success "Service account created"
    fi
    
    # Grant necessary roles
    print_status "Granting IAM roles..."
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/datastore.user"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/logging.logWriter"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/monitoring.metricWriter"
    
    print_success "IAM roles granted"
}

# Function to deploy using Cloud Build
deploy_with_cloud_build() {
    print_status "Deploying using Cloud Build..."
    
    cd backend
    gcloud builds submit --config cloudbuild.yaml \
        --substitutions=_SERVICE=$SERVICE_NAME,_REGION=$REGION
    
    print_success "Cloud Build deployment completed"
}

# Function to deploy to Cloud Run directly
deploy_to_cloud_run() {
    print_status "Building and deploying to Cloud Run..."
    
    cd backend
    
    # Build the image
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
    
    # Deploy to Cloud Run
    gcloud run deploy $SERVICE_NAME \
        --image gcr.io/$PROJECT_ID/$SERVICE_NAME \
        --platform managed \
        --region $REGION \
        --allow-unauthenticated \
        --memory 2Gi \
        --cpu 1 \
        --min-instances 0 \
        --max-instances 10 \
        --timeout 300 \
        --concurrency 80 \
        --set-env-vars PORT=8080,FLASK_ENV=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
        --service-account $SERVICE_ACCOUNT
    
    print_success "Cloud Run deployment completed"
}

# Function to deploy to Compute Engine
deploy_to_compute_engine() {
    print_status "Deploying to Compute Engine..."
    
    cd backend
    
    # Build the image
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$SERVICE_NAME
    
    # Create instance template
    gcloud compute instance-templates create-with-container $SERVICE_NAME-template \
        --machine-type e2-medium \
        --boot-disk-size 20GB \
        --image-family cos-stable \
        --image-project cos-cloud \
        --container-image gcr.io/$PROJECT_ID/$SERVICE_NAME \
        --container-restart-policy always \
        --container-env PORT=8080,FLASK_ENV=production,GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
        --service-account $SERVICE_ACCOUNT \
        --scopes cloud-platform \
        --tags http-server,https-server
    
    # Create managed instance group
    gcloud compute instance-groups managed create $SERVICE_NAME-group \
        --template $SERVICE_NAME-template \
        --size 1 \
        --zone $REGION-a
    
    # Create firewall rule for HTTP traffic
    if ! gcloud compute firewall-rules describe allow-$SERVICE_NAME-http &> /dev/null; then
        gcloud compute firewall-rules create allow-$SERVICE_NAME-http \
            --allow tcp:8080 \
            --source-ranges 0.0.0.0/0 \
            --target-tags http-server \
            --description "Allow HTTP traffic to SEC Document Scraper"
    fi
    
    print_success "Compute Engine deployment completed"
}

# Function to update frontend configuration
update_frontend_config() {
    print_status "Updating frontend configuration..."
    
    # Get the Cloud Run service URL
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
        --platform managed \
        --region $REGION \
        --format 'value(status.url)')
    
    if [ ! -z "$SERVICE_URL" ]; then
        print_status "Backend service URL: $SERVICE_URL"
        echo "Update your frontend configuration to use this URL"
        echo "For local development, you can set REACT_APP_API_BASE=$SERVICE_URL"
    fi
}

# Main deployment function
main() {
    print_status "Starting SEC Document Scraper deployment to Google Cloud"
    
    # Check deployment target
    DEPLOYMENT_TARGET=${1:-"cloud-run"}
    
    case $DEPLOYMENT_TARGET in
        "cloud-run")
            print_status "Deploying to Cloud Run (recommended)"
            ;;
        "compute-engine")
            print_status "Deploying to Compute Engine"
            ;;
        "cloud-build")
            print_status "Deploying using Cloud Build"
            ;;
        *)
            print_error "Invalid deployment target. Use: cloud-run, compute-engine, or cloud-build"
            exit 1
            ;;
    esac
    
    # Perform deployment steps
    check_gcloud
    setup_project
    create_service_account
    
    case $DEPLOYMENT_TARGET in
        "cloud-run")
            deploy_to_cloud_run
            update_frontend_config
            ;;
        "compute-engine")
            deploy_to_compute_engine
            ;;
        "cloud-build")
            deploy_with_cloud_build
            update_frontend_config
            ;;
    esac
    
    print_success "Deployment completed successfully!"
    print_status "Check the Google Cloud Console for your deployed service"
}

# Run main function with command line arguments
main "$@" 
#!/bin/bash
# Deployment script for Fraction Ball LMS to Firebase + Cloud Run

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="fractionball-lms"
REGION="us-central1"
SERVICE_NAME="fractionball-backend"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Fraction Ball LMS Deployment Script  ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed.${NC}"
    echo "Please install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if firebase-tools is installed
if ! command -v firebase &> /dev/null; then
    echo -e "${YELLOW}Warning: Firebase CLI is not installed.${NC}"
    echo "Installing Firebase CLI..."
    npm install -g firebase-tools
fi

# Check if logged in to gcloud
if ! gcloud auth print-identity-token &> /dev/null; then
    echo -e "${YELLOW}Please login to Google Cloud:${NC}"
    gcloud auth login
fi

# Set the project
echo -e "${GREEN}Setting project to ${PROJECT_ID}...${NC}"
gcloud config set project $PROJECT_ID

# Step 1: Build the Docker image
echo ""
echo -e "${GREEN}Step 1: Building Docker image...${NC}"
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:latest -f Dockerfile.production .

# Step 2: Push to Google Container Registry
echo ""
echo -e "${GREEN}Step 2: Pushing image to Container Registry...${NC}"
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:latest

# Step 3: Deploy to Cloud Run
echo ""
echo -e "${GREEN}Step 3: Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "DJANGO_SETTINGS_MODULE=fractionball.settings_production"

# Get the Cloud Run URL
CLOUD_RUN_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format='value(status.url)')
echo -e "${GREEN}Cloud Run deployed at: $CLOUD_RUN_URL${NC}"

# Step 4: Collect static files
echo ""
echo -e "${GREEN}Step 4: Collecting static files...${NC}"
python manage.py collectstatic --noinput --settings=fractionball.settings_production

# Step 5: Deploy to Firebase Hosting
echo ""
echo -e "${GREEN}Step 5: Deploying to Firebase Hosting...${NC}"
firebase deploy --only hosting

# Step 6: Deploy storage rules
echo ""
echo -e "${GREEN}Step 6: Deploying Firebase Storage rules...${NC}"
firebase deploy --only storage

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Deployment Complete!                 ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Cloud Run Backend: ${YELLOW}$CLOUD_RUN_URL${NC}"
echo -e "Firebase Hosting:  ${YELLOW}https://$PROJECT_ID.web.app${NC}"
echo ""










#!/bin/bash
# =============================================================================
# Setup Firebase Secrets in Google Cloud Secret Manager
# =============================================================================
# This script creates the necessary secrets for Cloud Run deployment.
# Run this ONCE before deploying to Cloud Run.
#
# Prerequisites:
#   1. gcloud CLI installed and authenticated
#   2. .env file with Firebase credentials in the fractionBallLMS directory
#   3. Appropriate IAM permissions to create secrets
#
# Usage:
#   cd fractionBallLMS
#   chmod +x scripts/setup_cloud_secrets.sh
#   ./scripts/setup_cloud_secrets.sh
# =============================================================================

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "Firebase Secret Manager Setup Script"
echo "=========================================="

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}Error: gcloud CLI is not installed.${NC}"
    echo "Install it from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if .env file exists
ENV_FILE=".env"
if [ ! -f "$ENV_FILE" ]; then
    ENV_FILE="../.env"
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}Error: .env file not found.${NC}"
        echo "Please run this script from the fractionBallLMS directory."
        exit 1
    fi
fi

echo -e "${GREEN}Found .env file: $ENV_FILE${NC}"

# Load .env file
source "$ENV_FILE"

# Verify required variables exist
REQUIRED_VARS=(
    "FIREBASE_PRIVATE_KEY"
    "FIREBASE_PRIVATE_KEY_ID"
    "FIREBASE_CLIENT_EMAIL"
    "FIREBASE_CLIENT_ID"
    "FIREBASE_CLIENT_X509_CERT_URL"
)

echo ""
echo "Checking required environment variables..."
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
        echo -e "${RED}  Missing: $var${NC}"
    else
        echo -e "${GREEN}  Found: $var${NC}"
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo ""
    echo -e "${RED}Error: Missing required variables in .env file.${NC}"
    exit 1
fi

# Get current project
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: No GCP project configured.${NC}"
    echo "Run: gcloud config set project YOUR_PROJECT_ID"
    exit 1
fi

echo ""
echo -e "Using GCP Project: ${GREEN}$PROJECT_ID${NC}"
echo ""

# Function to create or update a secret
create_secret() {
    local SECRET_NAME=$1
    local SECRET_VALUE=$2

    # Check if secret exists
    if gcloud secrets describe "$SECRET_NAME" &>/dev/null; then
        echo -e "${YELLOW}Updating existing secret: $SECRET_NAME${NC}"
        echo -n "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" --data-file=-
    else
        echo -e "${GREEN}Creating new secret: $SECRET_NAME${NC}"
        echo -n "$SECRET_VALUE" | gcloud secrets create "$SECRET_NAME" --data-file=-
    fi
}

# Create Django secret key (generate a new one for production)
echo "Creating/updating secrets..."
echo ""

DJANGO_SECRET="$(openssl rand -base64 50 | tr -d '\n')"
create_secret "DJANGO_SECRET_KEY" "$DJANGO_SECRET"

# Create Firebase secrets
create_secret "FIREBASE_PRIVATE_KEY" "$FIREBASE_PRIVATE_KEY"
create_secret "FIREBASE_PRIVATE_KEY_ID" "$FIREBASE_PRIVATE_KEY_ID"
create_secret "FIREBASE_CLIENT_EMAIL" "$FIREBASE_CLIENT_EMAIL"
create_secret "FIREBASE_CLIENT_ID" "$FIREBASE_CLIENT_ID"
create_secret "FIREBASE_CLIENT_X509_CERT_URL" "$FIREBASE_CLIENT_X509_CERT_URL"

echo ""
echo "=========================================="
echo -e "${GREEN}Secrets created successfully!${NC}"
echo "=========================================="

# Get project number for IAM binding
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format="value(projectNumber)")

echo ""
echo "Now granting Cloud Run access to secrets..."
echo ""

# Grant Cloud Run service account access to secrets
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SECRET_NAME in "DJANGO_SECRET_KEY" "FIREBASE_PRIVATE_KEY" "FIREBASE_PRIVATE_KEY_ID" "FIREBASE_CLIENT_EMAIL" "FIREBASE_CLIENT_ID" "FIREBASE_CLIENT_X509_CERT_URL"; do
    echo "Granting access to $SECRET_NAME..."
    gcloud secrets add-iam-policy-binding "$SECRET_NAME" \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet 2>/dev/null || true
done

echo ""
echo "=========================================="
echo -e "${GREEN}Setup complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Commit your changes: git add . && git commit -m 'Update deployment config'"
echo "  2. Push to trigger deployment: git push origin main"
echo "  3. Or manually deploy: gcloud builds submit --config cloudbuild.yaml"
echo ""
echo "To verify secrets were created:"
echo "  gcloud secrets list"
echo ""

#!/bin/bash
# Quick deployment script for Fraction Ball LMS
# 
# Usage:
#   ./scripts/quick-deploy.sh          # Fast deploy (uses existing image)
#   ./scripts/quick-deploy.sh build    # Build new image and deploy
#   ./scripts/quick-deploy.sh restart  # Just restart service (fastest)

set -e

PROJECT_ID="fractionball-lms"
REGION="us-central1"
SERVICE="fractionball-backend"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE}:latest"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${GREEN}🚀 Fraction Ball Quick Deploy${NC}"
echo "================================"

MODE=${1:-deploy}

case $MODE in
    "build")
        echo -e "${YELLOW}📦 Building new Docker image...${NC}"
        echo "⏱️  This takes ~2-3 minutes"
        
        # Build for AMD64 (Cloud Run)
        docker build --platform linux/amd64 -t $IMAGE -f Dockerfile.production .
        
        echo -e "${CYAN}📤 Pushing to Container Registry...${NC}"
        docker push $IMAGE
        
        echo -e "${GREEN}🚀 Deploying to Cloud Run...${NC}"
        gcloud run deploy $SERVICE \
            --image $IMAGE \
            --region $REGION \
            --platform managed \
            --allow-unauthenticated \
            --memory 1Gi \
            --set-env-vars "DJANGO_SETTINGS_MODULE=fractionball.settings_production,DEBUG=False,SECRET_KEY=fractionball-secret-key-prod-2024-stable,FIREBASE_PROJECT_ID=fractionball-lms,FIREBASE_STORAGE_BUCKET=fractionball-lms.firebasestorage.app"
        ;;
        
    "deploy")
        echo -e "${GREEN}⚡ Fast deploy using existing image...${NC}"
        echo "⏱️  This takes ~1-2 minutes"
        
        gcloud run deploy $SERVICE \
            --image $IMAGE \
            --region $REGION \
            --platform managed \
            --allow-unauthenticated \
            --memory 1Gi \
            --set-env-vars "DJANGO_SETTINGS_MODULE=fractionball.settings_production,DEBUG=False,SECRET_KEY=fractionball-secret-key-prod-2024-stable,FIREBASE_PROJECT_ID=fractionball-lms,FIREBASE_STORAGE_BUCKET=fractionball-lms.firebasestorage.app"
        ;;
        
    "restart")
        echo -e "${CYAN}🔄 Restarting service (new revision)...${NC}"
        echo "⏱️  This takes ~30-60 seconds"
        
        # Force new revision by updating an env var
        gcloud run services update $SERVICE \
            --region $REGION \
            --update-env-vars "RESTART_TIME=$(date +%s)"
        ;;
        
    *)
        echo "Usage: $0 [build|deploy|restart]"
        echo ""
        echo "  build   - Build new Docker image and deploy (2-3 min)"
        echo "  deploy  - Deploy using existing image (1-2 min)"
        echo "  restart - Just restart service (30-60 sec)"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Done!${NC}"
echo "🌐 https://fractionball-backend-110595744029.us-central1.run.app"

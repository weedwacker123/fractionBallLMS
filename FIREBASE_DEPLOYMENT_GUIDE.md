# Firebase & Cloud Run Deployment Guide

## 🚀 Complete Guide to Deploying Fraction Ball LMS

This guide covers deploying the Fraction Ball LMS to Firebase Hosting with a Cloud Run backend.

---

## 📋 Prerequisites

Before deploying, ensure you have:

1. **Google Cloud Account** with billing enabled
2. **Firebase Project** (we're using `fractionball-lms`)
3. **Node.js** (v18 or higher)
4. **Docker** installed
5. **gcloud CLI** installed
6. **Firebase CLI** installed

### Install Required Tools

```bash
# Install gcloud CLI (macOS)
brew install google-cloud-sdk

# Install Firebase CLI
npm install -g firebase-tools

# Verify installations
gcloud --version
firebase --version
docker --version
```

---

## 🔧 Step 1: Firebase Console Setup

### 1.1 Create/Access Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click **"Add Project"** or select existing project (`fractionball-lms`)
3. Enable Google Analytics (optional but recommended)

### 1.2 Enable Authentication

1. Go to **Authentication** → **Sign-in method**
2. Enable the following providers:

   **Google:**
   - Click "Google"
   - Toggle "Enable"
   - Set your project support email
   - Click "Save"

   **Email/Password:**
   - Click "Email/Password"
   - Toggle "Enable"
   - Click "Save"

### 1.3 Set Up Firebase Storage

1. Go to **Storage** → **Get Started**
2. Select "Start in production mode"
3. Choose location: `us-central1`
4. Click "Done"

### 1.4 Deploy Storage Rules

After setup, deploy the security rules:
```bash
firebase deploy --only storage
```

### 1.5 Get Service Account Credentials

1. Go to **Project Settings** (gear icon) → **Service Accounts**
2. Click **"Generate new private key"**
3. Save the JSON file as `firebase-service-account.json` in your project root
4. **IMPORTANT:** Add this file to `.gitignore` - never commit it!

---

## 🔧 Step 2: Google Cloud Console Setup

### 2.1 Enable Required APIs

Go to [Google Cloud Console](https://console.cloud.google.com) and enable:

```bash
# Or run these commands:
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

### 2.2 Create Cloud SQL Database (Optional but Recommended)

For production, use Cloud SQL instead of SQLite:

```bash
# Create PostgreSQL instance
gcloud sql instances create fractionball-db \
    --database-version=POSTGRES_14 \
    --tier=db-f1-micro \
    --region=us-central1

# Create database
gcloud sql databases create fractionball --instance=fractionball-db

# Create user
gcloud sql users create fractionball_user \
    --instance=fractionball-db \
    --password=YOUR_SECURE_PASSWORD
```

### 2.3 Set Up Secret Manager

Store sensitive configuration in Secret Manager:

```bash
# Create secrets
echo -n "your-django-secret-key" | gcloud secrets create django-secret-key --data-file=-
echo -n "postgres://user:pass@host/db" | gcloud secrets create database-url --data-file=-
echo -n "your-firebase-private-key" | gcloud secrets create firebase-private-key --data-file=-
```

---

## 🔧 Step 3: Configure Environment Variables

### 3.1 Create Production .env File

Create `.env.production`:

```bash
# Django Settings
DEBUG=0
SECRET_KEY=your-super-secret-production-key-here
DJANGO_SETTINGS_MODULE=fractionball.settings_production

# Database (Cloud SQL)
DATABASE_URL=postgres://fractionball_user:PASSWORD@/fractionball?host=/cloudsql/PROJECT_ID:REGION:INSTANCE_NAME

# Firebase Configuration
FIREBASE_PROJECT_ID=fractionball-lms
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@fractionball-lms.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_CLIENT_X509_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40fractionball-lms.iam.gserviceaccount.com
FIREBASE_STORAGE_BUCKET=fractionball-lms.appspot.com

# Cloud Run
CLOUD_RUN_SERVICE_URL=https://fractionball-backend-xxxxx-uc.a.run.app
```

---

## 🚀 Step 4: Deploy

### Option A: Automated Deployment

```bash
# Make the script executable
chmod +x scripts/deploy.sh

# Run deployment
./scripts/deploy.sh
```

### Option B: Manual Deployment

#### 4.1 Build Docker Image

```bash
# Build for Cloud Run
docker build -t gcr.io/fractionball-lms/fractionball-backend:latest -f Dockerfile.production .
```

#### 4.2 Push to Container Registry

```bash
# Configure Docker for GCR
gcloud auth configure-docker

# Push image
docker push gcr.io/fractionball-lms/fractionball-backend:latest
```

#### 4.3 Deploy to Cloud Run

```bash
gcloud run deploy fractionball-backend \
    --image gcr.io/fractionball-lms/fractionball-backend:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi \
    --set-env-vars "DJANGO_SETTINGS_MODULE=fractionball.settings_production" \
    --set-secrets "SECRET_KEY=django-secret-key:latest"
```

#### 4.4 Collect Static Files

```bash
python manage.py collectstatic --noinput --settings=fractionball.settings_production
```

#### 4.5 Deploy to Firebase Hosting

```bash
firebase login
firebase deploy --only hosting
```

---

## 🌐 Step 5: Custom Domain Setup (Optional)

### 5.1 Firebase Hosting Custom Domain

1. Go to Firebase Console → Hosting
2. Click "Add custom domain"
3. Enter your domain: `fractionball.com`
4. Follow DNS verification steps
5. Add provided DNS records to your domain registrar

### 5.2 Cloud Run Custom Domain

```bash
gcloud run domain-mappings create \
    --service fractionball-backend \
    --domain api.fractionball.com \
    --region us-central1
```

---

## 📊 Step 6: Post-Deployment

### 6.1 Run Database Migrations

```bash
# Connect to Cloud Run service and run migrations
gcloud run jobs create migrate-db \
    --image gcr.io/fractionball-lms/fractionball-backend:latest \
    --region us-central1 \
    --set-env-vars "DJANGO_SETTINGS_MODULE=fractionball.settings_production" \
    --command "python" \
    --args "manage.py,migrate"

gcloud run jobs execute migrate-db --region us-central1
```

### 6.2 Create Superuser

```bash
# Create admin user
gcloud run jobs create create-superuser \
    --image gcr.io/fractionball-lms/fractionball-backend:latest \
    --region us-central1 \
    --set-env-vars "DJANGO_SETTINGS_MODULE=fractionball.settings_production" \
    --command "python" \
    --args "manage.py,createsuperuser,--noinput,--username,admin,--email,admin@fractionball.com"

gcloud run jobs execute create-superuser --region us-central1
```

### 6.3 Verify Deployment

```bash
# Check Cloud Run service
curl https://fractionball-backend-xxxxx-uc.a.run.app/health/

# Check Firebase Hosting
curl https://fractionball-lms.web.app/
```

---

## 🔍 Monitoring & Troubleshooting

### View Cloud Run Logs

```bash
gcloud run services logs read fractionball-backend --region us-central1
```

### View in Console

1. **Cloud Run Dashboard:** https://console.cloud.google.com/run
2. **Firebase Console:** https://console.firebase.google.com
3. **Cloud Logging:** https://console.cloud.google.com/logs

### Common Issues

**Issue: 502 Bad Gateway**
- Check Cloud Run logs for errors
- Verify environment variables are set correctly
- Ensure DATABASE_URL is valid

**Issue: Static files not loading**
- Run `collectstatic` again
- Redeploy to Firebase Hosting
- Check browser console for CORS errors

**Issue: Authentication failing**
- Verify Firebase credentials in Secret Manager
- Check CORS settings include your domains
- Ensure Firebase Auth is enabled

---

## 💰 Cost Optimization

### Firebase Pricing

- **Hosting:** Free tier includes 10GB storage, 360MB/day transfer
- **Storage:** Free tier includes 5GB storage, 1GB/day download
- **Authentication:** Free for most use cases

### Cloud Run Pricing

- **Free tier:** 2 million requests/month
- **CPU:** $0.00002400/vCPU-second
- **Memory:** $0.00000250/GiB-second

**Estimated monthly cost for 1,000 teachers:** ~$25-50/month

### Optimize Costs

```bash
# Set minimum instances to 0 (cold starts but free when not used)
gcloud run services update fractionball-backend \
    --min-instances 0 \
    --region us-central1

# Use smaller memory if possible
gcloud run services update fractionball-backend \
    --memory 256Mi \
    --region us-central1
```

---

## 🔄 CI/CD Setup (Optional)

### GitHub Actions Workflow

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Firebase & Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Auth to Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Deploy to Cloud Run
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: fractionball-backend
          region: us-central1
          image: gcr.io/fractionball-lms/fractionball-backend:${{ github.sha }}
      
      - name: Deploy to Firebase
        uses: FirebaseExtended/action-hosting-deploy@v0
        with:
          repoToken: ${{ secrets.GITHUB_TOKEN }}
          firebaseServiceAccount: ${{ secrets.FIREBASE_SERVICE_ACCOUNT }}
          projectId: fractionball-lms
```

---

## 📝 Quick Reference

| Service | URL |
|---------|-----|
| Firebase Console | https://console.firebase.google.com/project/fractionball-lms |
| Cloud Run Console | https://console.cloud.google.com/run?project=fractionball-lms |
| Production Site | https://fractionball-lms.web.app |
| API Endpoint | https://fractionball-backend-xxxxx-uc.a.run.app |
| Admin Panel | https://fractionball-lms.web.app/admin/ |

---

## ✅ Deployment Checklist

- [ ] Firebase project created
- [ ] Google authentication enabled
- [ ] Email/Password authentication enabled
- [ ] Firebase Storage configured
- [ ] Storage rules deployed
- [ ] Service account JSON downloaded
- [ ] Cloud SQL database created (optional)
- [ ] Secrets stored in Secret Manager
- [ ] Docker image built and pushed
- [ ] Cloud Run service deployed
- [ ] Static files collected
- [ ] Firebase Hosting deployed
- [ ] Database migrations run
- [ ] Superuser created
- [ ] Custom domain configured (optional)
- [ ] Health check verified

---

**Need help?** Check the [Firebase Documentation](https://firebase.google.com/docs) or [Cloud Run Documentation](https://cloud.google.com/run/docs).










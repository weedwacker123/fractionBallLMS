# FractionBall LMS

Learning Management System for FractionBall — Django 5.1 backend serving educational content from Firestore.

## Architecture

```
User Browser
    ↓
Vercel (reverse proxy — just URL rewrites, no compute)
    ↓
Google Cloud Run (Django + Gunicorn in Docker)
    ↓
Firestore (content data) + Firebase Auth (user auth) + Cloud Storage (files)
```

- **Framework:** Django 5.1 + Django REST Framework
- **Database:** Firestore (primary content), SQLite (local dev), PostgreSQL (optional for Cloud Run)
- **Auth:** Firebase JWT tokens verified by custom middleware
- **Frontend:** Django templates + Tailwind CSS + vanilla JS
- **Static files:** WhiteNoise (served directly from Django)
- **Deployment:** Docker → Google Cloud Run (Vercel is just a proxy)

### Important: Vercel does NOT run Django

Vercel only acts as a **reverse proxy**. The `vercel.json` rewrites all requests to `https://fractionball-backend-110595744029.us-central1.run.app`. Vercel has no serverless functions, no Docker, no Python runtime — it just forwards traffic.

## Quick Start (Local Development)

### Option A: Without Docker (simplest)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
npm install                     # For Tailwind CSS
python manage.py migrate
python manage.py runserver      # http://localhost:8000
```

### Option B: With Docker Compose (full stack with PostgreSQL + Redis)
```bash
make build    # Build containers
make up       # Start everything → http://localhost:8000
```

Default dev credentials: `admin` / `admin123` (created automatically by Docker entrypoint)

## Commands

### Without Docker
| Command | What it does |
|---------|-------------|
| `python manage.py runserver` | Start dev server (port 8000) |
| `python manage.py migrate` | Run database migrations |
| `python manage.py makemigrations` | Create new migrations |
| `python manage.py collectstatic` | Collect static files to `staticfiles/` |
| `pytest` | Run tests |
| `pytest --cov=.` | Run tests with coverage |
| `black .` | Format Python code |
| `isort .` | Sort imports |
| `flake8 .` | Lint check |

### With Docker (via Makefile)
| Command | What it does |
|---------|-------------|
| `make up` | Start dev environment (PostgreSQL + Redis + Django) |
| `make down` | Stop everything |
| `make logs` | Tail container logs |
| `make test` | Run tests inside container |
| `make lint` | Run linters inside container |
| `make format` | Auto-format code inside container |
| `make shell` | Django shell inside container |
| `make migrate` | Run migrations inside container |
| `make seed` | Seed database with sample data |
| `make clean` | Stop containers AND delete volumes (destructive) |

## Project Structure

```
fractionball/                 # Django project settings
├── settings.py               # Development settings (DEBUG=True, SQLite)
├── settings_production.py    # Production settings (Cloud Run, PostgreSQL)
├── urls.py                   # Root URL config
└── wsgi.py                   # WSGI entry point (used by Gunicorn)

accounts/                     # User auth app
├── models.py                 # Custom User model (firebase_uid, role, school)
├── middleware.py              # FirebaseAuthMiddleware (JWT verification)
└── authentication.py         # DRF FirebaseAuthentication class

content/                      # Core content app
├── firestore_service.py      # Firestore client & activity queries
├── taxonomy_service.py       # Taxonomy caching (30s TTL)
├── v4_views.py               # Main views: home(), search_activities()
├── cms_views.py              # CMS-related views
└── firestore_adapters.py     # ORM ↔ Firestore adapters

api/                          # REST API endpoints
config/                       # System config & feature flags
templates/                    # Django HTML templates (Tailwind CSS)
static/                       # Static assets (CSS, JS, images)
```

## Deployment

### How it works

```
1. Build Docker image (Dockerfile.production)
2. Push image to Google Container Registry
3. Deploy to Google Cloud Run
```

Vercel auto-deploys its proxy config when you push `vercel.json` changes, but the actual Django app deploys to Cloud Run.

### Deploy to Cloud Run

**Option A: Quick deploy script (recommended)**
```bash
# Build new Docker image and deploy (~2-3 min)
./scripts/quick-deploy.sh build

# Re-deploy existing image with new config (~1-2 min)
./scripts/quick-deploy.sh deploy

# Just restart the service (~30-60 sec)
./scripts/quick-deploy.sh restart
```

**Option B: Cloud Build (CI/CD style)**
```bash
gcloud builds submit --config cloudbuild.yaml
```
This builds the Docker image in the cloud (no local Docker needed), pushes it, and deploys to Cloud Run with secrets from Google Secret Manager.

**Option C: Full manual deploy**
```bash
# 1. Build for linux/amd64 (Cloud Run requires this)
docker build --platform linux/amd64 -t gcr.io/fractionball-lms/fractionball-backend:latest -f Dockerfile.production .

# 2. Push to Container Registry
docker push gcr.io/fractionball-lms/fractionball-backend:latest

# 3. Deploy to Cloud Run
gcloud run deploy fractionball-backend \
    --image gcr.io/fractionball-lms/fractionball-backend:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 512Mi
```

### Prerequisites for deploying

1. **Google Cloud SDK** (`gcloud`) installed and authenticated
2. **Docker** installed (for building images locally — not needed if using Cloud Build)
3. **GCP project access** to `fractionball-lms`
4. **Secrets in Secret Manager** (run `./scripts/setup_cloud_secrets.sh` once for initial setup)

### Production URLs
- **Cloud Run backend:** `https://fractionball-backend-110595744029.us-central1.run.app`
- **Vercel proxy (user-facing):** Check Vercel dashboard for the custom domain

## Environment Variables

### Local development (`.env` file)
Key variables (see `env.example` for full list):
```bash
DEBUG=1
SECRET_KEY=your-dev-secret-key
STORAGE_BACKEND=local           # Use local file storage for dev
USE_FIRESTORE=true              # Read content from Firestore
FIREBASE_PROJECT_ID=fractionball-lms
FIREBASE_PRIVATE_KEY=...        # Firebase service account key
FIREBASE_CLIENT_EMAIL=...
FIREBASE_STORAGE_BUCKET=fractionball-lms.firebasestorage.app
```

### Production (Google Secret Manager)
Sensitive secrets are stored in Secret Manager and injected by Cloud Run at deploy time. Non-sensitive config is set as env vars in `cloudbuild.yaml`:
- `DJANGO_SETTINGS_MODULE=fractionball.settings_production`
- `FIREBASE_PROJECT_ID`, `FIREBASE_STORAGE_BUCKET`, `USE_FIRESTORE`
- Secrets: `SECRET_KEY`, `FIREBASE_PRIVATE_KEY`, `FIREBASE_CLIENT_EMAIL`, etc.

## CI/CD

### GitHub Actions (`.github/workflows/ci.yml`)
Runs on push/PR to `main` or `develop`:
- **Lint job:** black, isort, flake8
- **Test job:** pytest with PostgreSQL + Redis services, coverage uploaded to Codecov

### Deployment is manual
There is no auto-deploy on push. After merging to `main`, deploy manually:
```bash
./scripts/quick-deploy.sh build
```

## Coding Standards

- **Formatter:** Black (default config)
- **Import sorting:** isort (profile=black)
- **Linter:** flake8 (max-line-length=88, ignores E203,W503)
- **Pre-commit hooks:** Install with `make install-hooks` or `pre-commit install`

## Key Concepts

### Hybrid data architecture
- `USE_FIRESTORE=true` (default): Content comes from Firestore (managed by the CMS)
- `USE_FIRESTORE=false`: Falls back to Django ORM (SQLite/PostgreSQL)
- User accounts always use Django ORM

### Dynamic taxonomy filters
- The CMS defines taxonomy types (grade, topic, court, standard, etc.) in a `taxonomies` Firestore collection
- `taxonomy_service.py` caches these for 30 seconds
- `get_all_taxonomy_categories()` auto-discovers new types — no code changes needed when adding taxonomy types in the CMS

### Firebase Auth flow
1. User signs in via Firebase Auth SDK (client-side)
2. Frontend sends JWT token in `Authorization: Bearer <token>` header
3. `FirebaseAuthMiddleware` verifies the token with Firebase Admin SDK
4. Matched to Django `User` model via `firebase_uid` field

## GitHub

- **Repo:** `https://github.com/weedwacker123/fractionBallLMS`
- **Branch:** `main` (single branch)
- **CI:** GitHub Actions on push/PR (lint + test)

## For New Developers

1. Clone the repo
2. Copy `env.example` to `.env` and fill in Firebase credentials (ask the team lead)
3. Run `pip install -r requirements.txt` (in a venv) and `npm install`
4. Run `python manage.py migrate && python manage.py runserver`
5. Open http://localhost:8000
6. To deploy: install `gcloud` CLI, authenticate, then run `./scripts/quick-deploy.sh build`
7. Vercel proxy config auto-deploys when you push `vercel.json` changes — no action needed for most changes

### Access needed
- **GitHub:** Write access to `weedwacker123/fractionBallCMS` and `weedwacker123/fractionBallLMS`
- **Google Cloud:** IAM access to project `fractionball-lms` (for Cloud Run deploys)
- **Vercel:** Team member on the Vercel org (for proxy config changes)
- **Firebase:** Access to `fractionball-lms` Firebase project (for Auth, Firestore rules)

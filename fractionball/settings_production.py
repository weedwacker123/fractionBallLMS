"""
Production settings for Fraction Ball LMS
Configured for Google Cloud Run + Firebase
"""

import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# SECURITY SETTINGS - PRODUCTION
# =============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Allowed hosts for Cloud Run and Firebase Hosting
ALLOWED_HOSTS = [
    '.run.app',  # Cloud Run domains
    '.fractionball.com',  # Your custom domain
    'fractionball.com',
    'www.fractionball.com',
    'fractionball-lms.web.app',  # Firebase Hosting
    'fractionball-lms.firebaseapp.com',  # Firebase Hosting
    '.web.app',  # Firebase Hosting wildcard
    '.firebaseapp.com',  # Firebase Hosting wildcard
    'localhost',  # For health checks
]

# Add Cloud Run service URL if set
CLOUD_RUN_SERVICE_URL = config('CLOUD_RUN_SERVICE_URL', default='')
if CLOUD_RUN_SERVICE_URL:
    ALLOWED_HOSTS.append(CLOUD_RUN_SERVICE_URL.replace('https://', '').replace('http://', ''))

# Security headers
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# HTTPS settings (Cloud Run handles SSL termination)
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Session Security
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 28800  # 8 hours
SESSION_COOKIE_NAME = '__session'  # Firebase Hosting only forwards cookies named __session

# CSRF Security
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False  # Must be False to allow JavaScript access for forms
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_DOMAIN = None  # Let the cookie be set for the current domain
CSRF_USE_SESSIONS = True  # Store CSRF token in session for better proxy compatibility

# Session cookie domain
SESSION_COOKIE_DOMAIN = None  # Let the cookie be set for the current domain

CSRF_TRUSTED_ORIGINS = [
    'https://fractionball-lms.web.app',
    'https://fractionball-lms.firebaseapp.com',
    'https://fractionball-admin.web.app',  # FireCMS admin
    'https://fractionball-admin.firebaseapp.com',  # FireCMS admin
    'https://fractionball-backend-110595744029.us-central1.run.app',
    'https://*.fractionball.com',
    'https://*.run.app',
    'https://*.us-central1.run.app',
    'https://*.web.app',
    'https://*.firebaseapp.com',
]

# Add Cloud Run URL to CSRF trusted origins
if CLOUD_RUN_SERVICE_URL:
    CSRF_TRUSTED_ORIGINS.append(CLOUD_RUN_SERVICE_URL)

# =============================================================================
# APPLICATION DEFINITION
# =============================================================================

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
]

LOCAL_APPS = [
    'accounts',
    'api',
    'content',
    'config',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'accounts.middleware.FirebaseAuthMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'fractionball.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'content.context_processors.menu_context',
                'content.context_processors.site_config_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'fractionball.wsgi.application'

# =============================================================================
# DATABASE - Cloud SQL or PostgreSQL
# =============================================================================

# Parse DATABASE_URL for Cloud SQL connection
DATABASE_URL = config('DATABASE_URL', default='')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    # Fallback to SQLite for testing (not recommended for production)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# =============================================================================
# CACHE - Redis (Cloud Memorystore) or in-memory
# =============================================================================

REDIS_URL = config('REDIS_URL', default='')

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
else:
    # Use local memory cache for simpler deployments
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }

# =============================================================================
# AUTHENTICATION
# =============================================================================

AUTH_USER_MODEL = 'accounts.User'

# Authentication backends - needed for Django admin and session-based auth
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Login URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================================
# INTERNATIONALIZATION
# =============================================================================

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC FILES - Firebase Hosting / Cloud Storage
# =============================================================================

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# WhiteNoise for serving static files efficiently
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files (user uploads go to Firebase Storage)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# =============================================================================
# REST FRAMEWORK
# =============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'accounts.authentication.FirebaseAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'auth': '300/hour',
        'library': '500/hour',
        'upload': '50/hour',
        'admin': '200/hour',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Fraction Ball Teacher LMS API',
    'DESCRIPTION': 'API for Fraction Ball Teacher Learning Management System',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# =============================================================================
# CORS SETTINGS
# =============================================================================

CORS_ALLOWED_ORIGINS = [
    'https://fractionball.com',
    'https://www.fractionball.com',
    'https://fractionball-lms.web.app',
    'https://fractionball-lms.firebaseapp.com',
    'https://fractionball-admin.web.app',
    'https://fractionball-admin.firebaseapp.com',
]

# Add Cloud Run URL to CORS
if CLOUD_RUN_SERVICE_URL:
    CORS_ALLOWED_ORIGINS.append(CLOUD_RUN_SERVICE_URL)

CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# FIREBASE CONFIGURATION
# =============================================================================

FIREBASE_CONFIG = {
    'type': 'service_account',
    'project_id': config('FIREBASE_PROJECT_ID', default='fractionball-lms'),
    'private_key_id': config('FIREBASE_PRIVATE_KEY_ID', default=''),
    'private_key': config('FIREBASE_PRIVATE_KEY', default='').replace('\\n', '\n'),
    'client_email': config('FIREBASE_CLIENT_EMAIL', default=''),
    'client_id': config('FIREBASE_CLIENT_ID', default=''),
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': config('FIREBASE_CLIENT_X509_CERT_URL', default=''),
}

# Firebase Storage
FIREBASE_STORAGE_BUCKET = config('FIREBASE_STORAGE_BUCKET', default='fractionball-lms.appspot.com')

# Use Firebase for all storage in production
STORAGE_BACKEND = 'firebase'

# =============================================================================
# LOGGING - Cloud Logging compatible
# =============================================================================

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            'format': '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(module)s", "message": "%(message)s"}',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# =============================================================================
# DEFAULT PRIMARY KEY
# =============================================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# Initialize Firebase Admin SDK
# =============================================================================

try:
    import firebase_init
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not initialize Firebase: {e}")





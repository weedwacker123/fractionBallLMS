"""
Django settings for fractionball project.
"""

import os
from pathlib import Path
from decouple import config
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-g*hlfw6y4ivp0_*##4mja%9d@9^=30eo248o07htj8sr31m5jh')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0').split(',')

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)

# HTTPS Settings (for production)
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=False, cast=bool)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Detect if running in production (Cloud Run sets this)
IS_PRODUCTION = config('GAE_APPLICATION', default='') != '' or config('K_SERVICE', default='') != '' or 'fractionball' in config('ALLOWED_HOSTS', default='')

# Session Security - secure cookies in production
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=IS_PRODUCTION, cast=bool)
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=28800, cast=int)  # 8 hours

# CSRF Security - secure cookies in production
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=IS_PRODUCTION, cast=bool)
CSRF_COOKIE_HTTPONLY = False  # Must be False so JavaScript can read it for AJAX requests
CSRF_COOKIE_SAMESITE = 'Lax'

# Parse CSRF_TRUSTED_ORIGINS - supports comma, space, or semicolon as separators
_csrf_origins_raw = config('CSRF_TRUSTED_ORIGINS', default='http://localhost:8000')
# Replace common separators with comma
import re
_csrf_origins_normalized = re.sub(r'[;\s]+', ',', _csrf_origins_raw)
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in _csrf_origins_normalized.split(',')
    if origin.strip()
]

# Always include Firebase domains (needed for production deployment)
_firebase_origins = [
    'https://fractionball-lms.web.app',
    'https://fractionball-lms.firebaseapp.com',
    'https://fractionball-backend-110595744029.us-central1.run.app',
]
for origin in _firebase_origins:
    if origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(origin)

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com", "https://unpkg.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https:")
CSP_CONNECT_SRC = ("'self'", "https:")
CSP_FRAME_SRC = ("'none'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)

# Application definition
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
            ],
        },
    },
]

WSGI_APPLICATION = 'fractionball.wsgi.application'

# Database
# Force SQLite for local development (no Docker or PostgreSQL required)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Redis Cache (use dummy cache for local development without Redis)
REDIS_URL = config('REDIS_URL', default='')

if REDIS_URL and not DEBUG:
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
    # Use dummy cache for local development (no Redis required)
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Authentication backends - needed for Django admin and session auth
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Login URLs
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework
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
        'anon': config('THROTTLE_ANON', default='100/hour'),
        'user': config('THROTTLE_USER', default='1000/hour'),
        'auth': config('THROTTLE_AUTH', default='300/hour'),
        'library': config('THROTTLE_LIBRARY', default='500/hour'),
        'upload': config('THROTTLE_UPLOAD', default='50/hour'),
        'admin': config('THROTTLE_ADMIN', default='200/hour'),
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Spectacular settings for API documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Fraction Ball Teacher LMS API',
    'DESCRIPTION': 'API for Fraction Ball Teacher Learning Management System',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# CORS settings
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000,http://127.0.0.1:8000').split(',')
CORS_ALLOW_CREDENTIALS = True

# Always include Firebase domains in CORS
for origin in _firebase_origins:
    if origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(origin)

# Firebase Configuration
FIREBASE_CONFIG = {
    'type': 'service_account',
    'project_id': config('FIREBASE_PROJECT_ID', default=''),
    'private_key_id': config('FIREBASE_PRIVATE_KEY_ID', default=''),
    'private_key': config('FIREBASE_PRIVATE_KEY', default='').replace('\\n', '\n'),
    'client_email': config('FIREBASE_CLIENT_EMAIL', default=''),
    'client_id': config('FIREBASE_CLIENT_ID', default=''),
    'auth_uri': config('FIREBASE_AUTH_URI', default='https://accounts.google.com/o/oauth2/auth'),
    'token_uri': config('FIREBASE_TOKEN_URI', default='https://oauth2.googleapis.com/token'),
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': config('FIREBASE_CLIENT_X509_CERT_URL', default=''),
}

# Firebase Storage Configuration
FIREBASE_STORAGE_BUCKET = config('FIREBASE_STORAGE_BUCKET', default='')
GOOGLE_APPLICATION_CREDENTIALS = config('GOOGLE_APPLICATION_CREDENTIALS', default='')

# Storage Backend Configuration
# Set to 'firebase' to enforce Firebase-only storage (recommended for production)
# Set to 'local' to use local storage only (for development/testing)
# Set to 'auto' to use Firebase with local fallback (legacy mode)
STORAGE_BACKEND = config('STORAGE_BACKEND', default='firebase')

# Set environment variable for Google Cloud SDK
if GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(GOOGLE_APPLICATION_CREDENTIALS):
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_APPLICATION_CREDENTIALS

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'] if not DEBUG else ['console'],
        'level': 'INFO',
    },
}

# Create logs directory
os.makedirs(BASE_DIR / 'logs', exist_ok=True)

# Initialize Firebase Admin SDK
# This must be done after all settings are configured
try:
    import firebase_init
except Exception as e:
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not initialize Firebase: {e}")
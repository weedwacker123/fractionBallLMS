# Fraction Ball Teacher LMS Platform

A production-grade Django-based Learning Management System for Fraction Ball's math education content, designed specifically for teachers to access, organize, and share video lessons and resources.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.12+ (for local development)
- Node.js 18+ (for Tailwind CSS)
- Firebase project with Authentication enabled

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fractionBallLMS
cp env.example .env
```

### 2. Firebase Setup

1. **Create Firebase Project:**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Create a new project
   - Enable Authentication with Email/Password and Google providers

2. **Generate Service Account Key:**
   - Go to Project Settings > Service Accounts
   - Click "Generate new private key"
   - Download the JSON file and save as `firebase-admin-sdk.json`

3. **Update Environment Variables:**
   Edit `.env` with your Firebase configuration:
   ```bash
   FIREBASE_PROJECT_ID=your-project-id
   FIREBASE_PRIVATE_KEY_ID=your-private-key-id
   FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n"
   FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
   # ... other Firebase config
   ```

### 3. Start Development Environment

```bash
# Build and start services
make up

# Or manually:
docker-compose up -d
```

### 4. Access the Application

- **API**: http://localhost:8000/api/
- **Admin**: http://localhost:8000/admin/
- **API Docs**: http://localhost:8000/api/docs/
- **Health Check**: http://localhost:8000/api/healthz/

### 5. Create Initial Data

```bash
# Seed database with sample schools and users
make seed

# Create superuser
make superuser
```

## 🏗️ Architecture

### Tech Stack

- **Backend**: Django 5.1 + Django REST Framework
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Authentication**: Firebase Auth (JWT verification)
- **Frontend**: Tailwind CSS + HTMX
- **Containerization**: Docker + Docker Compose

### Key Features

- **Firebase Authentication**: Email/Password + Google SSO
- **Role-Based Access Control**: Admin, School Admin, Teacher roles
- **School-Scoped Organization**: Users belong to schools/districts
- **RESTful API**: Comprehensive API with OpenAPI documentation
- **Responsive UI**: Modern, mobile-friendly interface

## 🔐 Authentication & Authorization

### Firebase Integration

The platform uses Firebase Authentication for user login with Django backend verification:

1. **Frontend**: Users authenticate via Firebase SDK
2. **Backend**: Django verifies Firebase ID tokens
3. **Database**: User profiles stored in Django with Firebase UID mapping

### User Roles

- **ADMIN**: System administrators (full access)
- **SCHOOL_ADMIN**: School administrators (school-scoped access)
- **TEACHER**: Teachers (content access and creation)

### API Authentication

```bash
# Include Firebase ID token in requests
Authorization: Bearer <firebase-id-token>
```

## 📡 API Endpoints

### Core Endpoints

- `GET /api/healthz/` - Health check
- `GET /api/me/` - Current user profile
- `PUT /api/me/` - Update profile

### Admin Endpoints (Admin only)

- `GET /api/schools/` - List schools
- `POST /api/schools/` - Create school
- `GET /api/users/` - List users
- `POST /api/users/` - Create user

### Documentation

- `GET /api/docs/` - Swagger UI
- `GET /api/redoc/` - ReDoc
- `GET /api/schema/` - OpenAPI schema

## 🛠️ Development

### Local Setup

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Setup pre-commit hooks
make install-hooks

# Build Tailwind CSS
npm run build-css
```

### Available Commands

```bash
make help          # Show available commands
make up            # Start development environment
make down          # Stop development environment
make logs          # Show container logs
make shell         # Open Django shell
make migrate       # Run database migrations
make test          # Run tests
make lint          # Run linting
make format        # Format code
make seed          # Seed database
make clean         # Clean up containers
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
docker-compose exec web pytest accounts/tests.py -v
```

### Code Quality

The project uses:
- **Black** for code formatting
- **isort** for import sorting
- **Flake8** for linting
- **pre-commit** hooks for automated checks

```bash
# Format code
make format

# Run linting
make lint
```

## 🏫 Data Models

### School

```python
class School(models.Model):
    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=100, unique=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### User

```python
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'System Admin'
        SCHOOL_ADMIN = 'SCHOOL_ADMIN', 'School Admin'
        TEACHER = 'TEACHER', 'Teacher'
    
    firebase_uid = models.CharField(max_length=128, unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
```

## 🔒 Security

- Firebase JWT token verification
- Role-based permissions
- CORS configuration
- Secure cookie settings
- Input validation and sanitization

## 🚀 Deployment

### Environment Variables

Required environment variables for production:

```bash
DEBUG=0
SECRET_KEY=your-production-secret-key
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://user:pass@host:port/dbname
REDIS_URL=redis://host:port/0
# Firebase configuration...
```

### Docker Production Build

```bash
# Build production image
docker build -t fractionball-lms .

# Run with production settings
docker run -p 8000:8000 --env-file .env.production fractionball-lms
```

## 📝 Testing

### Test Coverage

- Model tests for School and User
- Authentication tests for Firebase integration
- Permission tests for RBAC
- API endpoint tests
- Integration tests

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=.

# Specific app
pytest accounts/tests.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

### Code Style

- Follow PEP 8
- Use Black for formatting
- Add docstrings to functions and classes
- Write tests for new features

## 📄 License

This project is proprietary software developed for Fraction Ball.

## 🆘 Support

For development support:
- Check the [API documentation](http://localhost:8000/api/docs/)
- Review the test files for usage examples
- Contact the development team

---

**Built with ❤️ for math education**

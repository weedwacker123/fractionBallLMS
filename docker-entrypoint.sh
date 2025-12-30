#!/bin/bash
set -e

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Creating superuser if not exists..."
python manage.py shell << EOF
from accounts.models import User
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser(
        username='admin',
        email='admin@fractionball.com',
        password='admin123',
        firebase_uid='admin-local-dev',
        role='ADMIN'
    )
    print(f"Created superuser: {user.username}")
else:
    print("Superuser 'admin' already exists")
EOF

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120 --max-requests 500 fractionball.wsgi:application


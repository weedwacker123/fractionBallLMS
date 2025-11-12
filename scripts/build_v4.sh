#!/bin/bash
# Build script for Fraction Ball V4 Interface

set -e

echo "🎨 Building Fraction Ball V4 Interface..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
fi

# Build Tailwind CSS
echo "🎨 Building Tailwind CSS..."
npm run build-css-prod

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

echo ""
echo "✅ V4 Interface build complete!"
echo ""
echo "Next steps:"
echo "  1. Run: python manage.py runserver"
echo "  2. Open: http://localhost:8000/"
echo ""










#!/bin/bash
# Production Build Script for Fraction Ball LMS
# Builds Tailwind CSS and prepares static assets for production

set -e  # Exit on error

echo "=========================================="
echo "  Fraction Ball LMS - Production Build"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Node.js is installed
echo "Step 1: Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js is not installed${NC}"
    echo ""
    echo "Please install Node.js first:"
    echo "  macOS: brew install node"
    echo "  Or download from: https://nodejs.org/"
    echo ""
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✅ Node.js ${NODE_VERSION} is installed${NC}"
echo ""

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm is not installed${NC}"
    exit 1
fi

NPM_VERSION=$(npm --version)
echo -e "${GREEN}✅ npm ${NPM_VERSION} is installed${NC}"
echo ""

# Install dependencies
echo "Step 2: Installing Node.js dependencies..."
if [ ! -d "node_modules" ]; then
    echo "Running npm install..."
    npm install
else
    echo -e "${YELLOW}⚠️  node_modules already exists. Run 'npm install' manually if you need to update.${NC}"
fi
echo -e "${GREEN}✅ Dependencies ready${NC}"
echo ""

# Create output directory if it doesn't exist
echo "Step 3: Preparing output directories..."
mkdir -p static/dist
echo -e "${GREEN}✅ Output directory ready${NC}"
echo ""

# Build production CSS
echo "Step 4: Building production CSS with Tailwind..."
echo "This may take a moment..."
npm run build-css-prod
echo -e "${GREEN}✅ CSS built successfully${NC}"
echo ""

# Check if build was successful
if [ ! -f "static/dist/output.css" ]; then
    echo -e "${RED}❌ Build failed: output.css not found${NC}"
    exit 1
fi

FILE_SIZE=$(du -h static/dist/output.css | cut -f1)
echo -e "${GREEN}✅ Production CSS: ${FILE_SIZE}${NC}"
echo ""

# Collect static files for Django
echo "Step 5: Collecting Django static files..."
python3 manage.py collectstatic --noinput
echo -e "${GREEN}✅ Static files collected${NC}"
echo ""

# Verify the build
echo "Step 6: Verifying build..."
if [ -f "static/dist/output.css" ]; then
    echo -e "${GREEN}✅ CSS file exists: static/dist/output.css${NC}"
    echo "   Size: $(du -h static/dist/output.css | cut -f1)"
    echo "   Lines: $(wc -l < static/dist/output.css)"
else
    echo -e "${RED}❌ CSS file not found${NC}"
    exit 1
fi
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}  ✅ Production Build Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Update templates to use compiled CSS"
echo "2. Test the application locally"
echo "3. Deploy to production"
echo ""
echo "To rebuild CSS during development:"
echo "  npm run build-css (with --watch for auto-rebuild)"
echo ""
echo "To rebuild for production:"
echo "  npm run build-css-prod"
echo ""


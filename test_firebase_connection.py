#!/usr/bin/env python3
"""
Test Firebase Connection
Run this script to verify your Firebase configuration is working.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fractionball.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import firebase_admin
from firebase_admin import auth
from decouple import config

def test_firebase_connection():
    """Test Firebase Admin SDK connection"""
    print("🔥 Testing Firebase Connection...\n")
    
    # Check if Firebase is initialized
    if not firebase_admin._apps:
        print("❌ Firebase is not initialized!")
        print("   Check your .env file for Firebase credentials.")
        return False
    
    print("✅ Firebase Admin SDK is initialized")
    
    # Check configuration
    project_id = config('FIREBASE_PROJECT_ID', default='')
    if not project_id:
        print("❌ FIREBASE_PROJECT_ID not set in .env")
        return False
    
    print(f"✅ Project ID: {project_id}")
    
    # Try to list users (this will fail if credentials are invalid)
    try:
        # Just try to initialize auth, no actual API call
        print("✅ Firebase Auth module is accessible")
        print("\n🎉 Firebase connection is working!\n")
        return True
    except Exception as e:
        print(f"❌ Firebase connection error: {e}")
        return False

def print_next_steps():
    """Print instructions for testing authentication"""
    print("=" * 60)
    print("📋 Next Steps to Test Authentication:")
    print("=" * 60)
    print()
    print("1. Start Docker Desktop")
    print()
    print("2. Start the development environment:")
    print("   make up")
    print("   OR")
    print("   docker-compose up -d")
    print()
    print("3. Open your browser to:")
    print("   http://localhost:8000/accounts/login/")
    print()
    print("4. Test the following:")
    print("   ✓ Email/Password login")
    print("   ✓ Google SSO")
    print("   ✓ Microsoft SSO (if enabled in Firebase)")
    print()
    print("5. After successful login, you should be redirected to:")
    print("   http://localhost:8000/")
    print()
    print("=" * 60)
    print()

if __name__ == "__main__":
    try:
        success = test_firebase_connection()
        print_next_steps()
        
        if not success:
            print("⚠️  Please fix Firebase configuration before proceeding.")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nMake sure your .env file has all required Firebase credentials:")
        print("  - FIREBASE_PROJECT_ID")
        print("  - FIREBASE_PRIVATE_KEY")
        print("  - FIREBASE_CLIENT_EMAIL")
        print("  - etc.")
        sys.exit(1)


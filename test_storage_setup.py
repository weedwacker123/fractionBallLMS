#!/usr/bin/env python3
"""
Test script to verify Firebase Storage and Local Storage setup
Run this after setting up Firebase Storage bucket
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fractionball.settings')
django.setup()

from django.conf import settings
from content.services import FirebaseStorageService
from content.local_storage import get_local_storage
import firebase_admin


def test_firebase_storage():
    """Test Firebase Storage connection"""
    print("\n" + "=" * 60)
    print("🔥 Testing Firebase Storage")
    print("=" * 60)
    
    try:
        # Check if Firebase is initialized
        if firebase_admin._apps:
            print("✅ Firebase Admin SDK initialized")
        else:
            print("❌ Firebase Admin SDK not initialized")
            return False
        
        # Test Firebase Storage Service
        service = FirebaseStorageService()
        
        if service.bucket:
            print(f"✅ Storage bucket accessible: {service.bucket.name}")
            
            # Try to list files (tests permissions)
            try:
                blobs = list(service.bucket.list_blobs(max_results=1))
                print(f"✅ Storage permissions OK")
                print(f"   Files in bucket: {len(blobs)}")
                return True
            except Exception as e:
                if "404" in str(e) and "does not exist" in str(e):
                    print("❌ Storage bucket does not exist yet")
                    print("   👉 You need to create the bucket in Firebase Console")
                    print("   👉 See: FIREBASE_STORAGE_SETUP_NOW.md")
                else:
                    print(f"⚠️  Storage access error: {e}")
                return False
        else:
            print("❌ Storage bucket not initialized")
            return False
            
    except Exception as e:
        print(f"❌ Firebase Storage error: {e}")
        return False


def test_local_storage():
    """Test Local Storage"""
    print("\n" + "=" * 60)
    print("📁 Testing Local Storage")
    print("=" * 60)
    
    try:
        storage = get_local_storage()
        print(f"✅ Local storage initialized at: {storage.media_root}")
        
        # Check if directories exist
        directories = ['videos', 'resources', 'thumbnails', 'lesson-plans']
        for directory in directories:
            dir_path = storage.media_root / directory
            if dir_path.exists():
                print(f"✅ Directory exists: {directory}/")
            else:
                print(f"⚠️  Directory missing: {directory}/")
        
        return True
        
    except Exception as e:
        print(f"❌ Local storage error: {e}")
        return False


def print_configuration():
    """Print current configuration"""
    print("\n" + "=" * 60)
    print("⚙️  Current Configuration")
    print("=" * 60)
    
    # Firebase settings
    print("\nFirebase Settings:")
    if hasattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS'):
        creds_file = settings.GOOGLE_APPLICATION_CREDENTIALS
        print(f"  Service Account: {creds_file}")
        if os.path.exists(creds_file):
            print(f"  ✅ File exists")
        else:
            print(f"  ❌ File not found")
    else:
        print("  ❌ GOOGLE_APPLICATION_CREDENTIALS not set")
    
    if hasattr(settings, 'FIREBASE_STORAGE_BUCKET'):
        print(f"  Storage Bucket: {settings.FIREBASE_STORAGE_BUCKET}")
    else:
        print("  ❌ FIREBASE_STORAGE_BUCKET not set")
    
    # Project info
    firebase_config = getattr(settings, 'FIREBASE_CONFIG', {})
    project_id = firebase_config.get('project_id', 'NOT SET')
    print(f"  Project ID: {project_id}")
    
    # Local storage
    print("\nLocal Storage:")
    print(f"  Media Root: {settings.BASE_DIR / 'media'}")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 Storage Configuration Test")
    print("=" * 60)
    
    # Print configuration
    print_configuration()
    
    # Test local storage
    local_ok = test_local_storage()
    
    # Test Firebase storage
    firebase_ok = test_firebase_storage()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    
    if local_ok:
        print("✅ Local Storage: WORKING")
    else:
        print("❌ Local Storage: NOT WORKING")
    
    if firebase_ok:
        print("✅ Firebase Storage: WORKING")
        print("\n🎉 All systems go! Files will be uploaded to Firebase.")
    else:
        print("⚠️  Firebase Storage: NOT READY")
        print("\n💡 Files will use local storage until Firebase bucket is created.")
        print("   Follow the guide: FIREBASE_STORAGE_SETUP_NOW.md")
    
    print("\n" + "=" * 60)
    print("🌐 Website Status")
    print("=" * 60)
    print("Your website is running at: http://localhost:8000")
    print("Upload page: http://localhost:8000/upload/")
    print("\nThe system will:")
    if firebase_ok:
        print("  1. ✅ Upload files to Firebase Storage")
        print("  2. ⚠️  Fall back to local storage if Firebase fails")
    else:
        print("  1. ⚠️  Use local storage (Firebase not ready)")
        print("  2. ✅ Automatically switch to Firebase when configured")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()




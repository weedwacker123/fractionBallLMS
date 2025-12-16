"""
Firebase Admin SDK Initialization
This module initializes Firebase Admin SDK when Django starts
"""
import os
import logging
import firebase_admin
from firebase_admin import credentials
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials"""
    if firebase_admin._apps:
        logger.info("Firebase Admin SDK already initialized")
        return True
    
    try:
        # Try to use service account JSON file first (preferred method)
        if hasattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS') and settings.GOOGLE_APPLICATION_CREDENTIALS:
            if os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
                try:
                    logger.info(f"Loading Firebase credentials from: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
                    cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
                    
                    # Initialize with storage bucket if available
                    options = {}
                    if hasattr(settings, 'FIREBASE_STORAGE_BUCKET') and settings.FIREBASE_STORAGE_BUCKET:
                        options['storageBucket'] = settings.FIREBASE_STORAGE_BUCKET
                        logger.info(f"Setting storage bucket: {settings.FIREBASE_STORAGE_BUCKET}")
                    
                    firebase_admin.initialize_app(cred, options)
                    logger.info("✅ Firebase Admin SDK initialized successfully with service account JSON")
                    logger.info(f"✅ Storage bucket configured: {settings.FIREBASE_STORAGE_BUCKET}")
                    return True
                    
                except Exception as init_error:
                    logger.error(f"❌ Firebase initialization with JSON file failed: {init_error}")
                    import traceback
                    traceback.print_exc()
                    return False
            else:
                logger.error(f"❌ Firebase service account file not found: {settings.GOOGLE_APPLICATION_CREDENTIALS}")
        
        # Fall back to environment variables if JSON file didn't work
        logger.warning("Trying to initialize with environment variables...")
        project_id = settings.FIREBASE_CONFIG.get('project_id', '')
        private_key = settings.FIREBASE_CONFIG.get('private_key', '')
        
        if project_id and private_key and len(private_key) > 100:
            try:
                cred = credentials.Certificate(settings.FIREBASE_CONFIG)
                options = {}
                if hasattr(settings, 'FIREBASE_STORAGE_BUCKET') and settings.FIREBASE_STORAGE_BUCKET:
                    options['storageBucket'] = settings.FIREBASE_STORAGE_BUCKET
                
                firebase_admin.initialize_app(cred, options)
                logger.info("✅ Firebase Admin SDK initialized successfully with env variables")
                return True
                
            except Exception as init_error:
                logger.error(f"❌ Firebase initialization with env failed: {init_error}")
                return False
        else:
            logger.error("❌ Firebase credentials not properly configured in .env")
            logger.error("Set FIREBASE_PROJECT_ID and FIREBASE_PRIVATE_KEY in your .env file")
            return False
            
    except Exception as e:
        logger.error(f"❌ Firebase setup error: {e}")
        import traceback
        traceback.print_exc()
        return False

# Auto-initialize when module is imported
initialize_firebase()







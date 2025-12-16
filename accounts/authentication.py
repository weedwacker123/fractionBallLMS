import firebase_admin
from firebase_admin import auth, credentials
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import authentication, exceptions
import json
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Initialize Firebase Admin SDK
FIREBASE_INITIALIZED = False
if not firebase_admin._apps:
    try:
        # Try to use service account JSON file first (preferred method)
        if hasattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS') and settings.GOOGLE_APPLICATION_CREDENTIALS:
            import os
            if os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
                try:
                    cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
                    # Initialize with storage bucket if available
                    options = {}
                    if hasattr(settings, 'FIREBASE_STORAGE_BUCKET') and settings.FIREBASE_STORAGE_BUCKET:
                        options['storageBucket'] = settings.FIREBASE_STORAGE_BUCKET
                    
                    firebase_admin.initialize_app(cred, options)
                    FIREBASE_INITIALIZED = True
                    logger.info("✅ Firebase Admin SDK initialized successfully with service account JSON")
                except Exception as init_error:
                    logger.warning(f"⚠️  Firebase initialization with JSON file failed: {str(init_error)[:100]}...")
        
        # Fall back to environment variables if JSON file didn't work
        if not FIREBASE_INITIALIZED:
            # Check if Firebase config has valid credentials
            project_id = settings.FIREBASE_CONFIG.get('project_id', '')
            private_key = settings.FIREBASE_CONFIG.get('private_key', '')
            
            if project_id and private_key and len(private_key) > 100:  # Basic validation
                try:
                    # Create credentials from settings
                    cred = credentials.Certificate(settings.FIREBASE_CONFIG)
                    # Initialize with storage bucket if available
                    options = {}
                    if hasattr(settings, 'FIREBASE_STORAGE_BUCKET') and settings.FIREBASE_STORAGE_BUCKET:
                        options['storageBucket'] = settings.FIREBASE_STORAGE_BUCKET
                    
                    firebase_admin.initialize_app(cred, options)
                    FIREBASE_INITIALIZED = True
                    logger.info("✅ Firebase Admin SDK initialized successfully")
                except Exception as init_error:
                    logger.warning(f"⚠️  Firebase initialization failed: {str(init_error)[:100]}...")
                    logger.warning("Authentication will use frontend Firebase only")
            else:
                logger.warning("⚠️  Firebase credentials not properly configured in .env")
                logger.warning("Set FIREBASE_PROJECT_ID and FIREBASE_PRIVATE_KEY in your .env file")
    except Exception as e:
        logger.warning(f"⚠️  Firebase setup error: {str(e)[:100]}...")


class FirebaseAuthentication(authentication.BaseAuthentication):
    """
    Firebase JWT token authentication for DRF
    """
    
    def authenticate(self, request):
        """
        Authenticate the request using Firebase ID token
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return None
            
        try:
            # Extract token from "Bearer <token>" format
            auth_parts = auth_header.split()
            if len(auth_parts) != 2 or auth_parts[0].lower() != 'bearer':
                return None
                
            token = auth_parts[1]
            
            # Verify the Firebase ID token
            decoded_token = auth.verify_id_token(token)
            firebase_uid = decoded_token['uid']
            
            # Get or create user
            user = self.get_or_create_user(decoded_token)
            
            return (user, token)
            
        except auth.InvalidIdTokenError:
            raise exceptions.AuthenticationFailed('Invalid Firebase token')
        except auth.ExpiredIdTokenError:
            raise exceptions.AuthenticationFailed('Expired Firebase token')
        except Exception as e:
            logger.error(f"Firebase authentication error: {e}")
            raise exceptions.AuthenticationFailed('Authentication failed')
    
    def get_or_create_user(self, decoded_token):
        """
        Get or create user from Firebase token data
        """
        firebase_uid = decoded_token['uid']
        email = decoded_token.get('email', '')
        name = decoded_token.get('name', '')
        
        try:
            # Try to get existing user
            user = User.objects.get(firebase_uid=firebase_uid)
            return user
        except User.DoesNotExist:
            # User doesn't exist - in production, users should be created by admins
            # For development, we'll create a basic user
            logger.warning(f"User with Firebase UID {firebase_uid} not found in database")
            raise exceptions.AuthenticationFailed(
                'User not found. Please contact your administrator to create your account.'
            )
    
    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response.
        """
        return 'Bearer'

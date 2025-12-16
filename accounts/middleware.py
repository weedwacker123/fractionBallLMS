import logging
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from firebase_admin import auth
import firebase_admin

logger = logging.getLogger(__name__)
User = get_user_model()


class FirebaseAuthMiddleware(MiddlewareMixin):
    """
    Middleware to handle Firebase authentication for non-API requests
    """
    
    def process_request(self, request):
        """
        Process the request to set user from Firebase token if present
        """
        # Skip API requests (handled by DRF authentication)
        if request.path.startswith('/api/'):
            return None
        
        # Skip admin and upload management requests (use Django session auth)
        if request.path.startswith('/admin/') or request.path.startswith('/my-uploads/'):
            return None
            
        # Check for Firebase token in session or cookies
        firebase_token = request.session.get('firebase_token') or request.COOKIES.get('firebase_token')
        
        if firebase_token:
            try:
                # Verify the Firebase ID token
                decoded_token = auth.verify_id_token(firebase_token)
                firebase_uid = decoded_token['uid']
                
                # Get user from database
                user = User.objects.get(firebase_uid=firebase_uid)
                
                # Set user on request (similar to Django's AuthenticationMiddleware)
                request.user = user
                
            except (auth.InvalidIdTokenError, auth.ExpiredIdTokenError, User.DoesNotExist) as e:
                logger.debug(f"Firebase middleware authentication failed: {e}")
                # Clear invalid token
                if 'firebase_token' in request.session:
                    del request.session['firebase_token']
                pass  # Let Django's default authentication handle it
            except Exception as e:
                logger.error(f"Firebase middleware error: {e}")
                pass
        
        return None

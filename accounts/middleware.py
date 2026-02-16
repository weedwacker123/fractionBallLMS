import logging
import time
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.shortcuts import redirect
from firebase_admin import auth
import firebase_admin

logger = logging.getLogger(__name__)
User = get_user_model()

# Token cache duration in seconds (5 minutes)
TOKEN_CACHE_DURATION = 300


class FirebaseAuthMiddleware(MiddlewareMixin):
    """
    Middleware to handle Firebase authentication for non-API requests.
    Includes token caching to avoid Firebase verification on every request.
    """

    # Paths that don't require authentication (prefix match)
    PUBLIC_PATH_PREFIXES = [
        '/accounts/login/',
        '/accounts/django-login/',
        '/accounts/logout/',
        '/accounts/verify-token/',
        '/accounts/google-auth/',
        '/api/',
        '/admin/',
        '/static/',
        '/faq/',
        '/search/',
        '/community/',
        '/health/',
    ]

    # Exact paths that don't require authentication
    PUBLIC_EXACT_PATHS = [
        '/',
        '/favicon.ico',
    ]

    def _is_public_path(self, path):
        """Check if the path is public (doesn't require authentication)"""
        # Check exact matches first
        if path in self.PUBLIC_EXACT_PATHS:
            return True
        # Check prefix matches
        for public_path in self.PUBLIC_PATH_PREFIXES:
            if path.startswith(public_path):
                return True
        return False

    def process_request(self, request):
        """
        Process the request to set user from Firebase token if present.
        Uses session caching to avoid Firebase verification on every request.

        Note: Django's AuthenticationMiddleware runs after this and may also
        set request.user based on the session. Since verify_token calls Django's
        login(), both systems should be in sync.
        """
        is_public = self._is_public_path(request.path)

        # Check for cached auth in session first
        cached_user_id = request.session.get('cached_user_id')
        cache_expiry = request.session.get('auth_cache_expiry', 0)

        # If we have a valid cache, use it
        if cached_user_id and time.time() < cache_expiry:
            try:
                user = User.objects.get(id=cached_user_id)
                request.user = user
                return None  # Allow request to proceed
            except User.DoesNotExist:
                # Cache is stale, clear it
                self._clear_auth_cache(request)

        # Check for Firebase token in session or cookies
        firebase_token = request.session.get('firebase_token') or request.COOKIES.get('firebase_token')

        if firebase_token:
            try:
                # Verify the Firebase ID token
                decoded_token = auth.verify_id_token(firebase_token)
                firebase_uid = decoded_token['uid']

                # Get user from database
                user = User.objects.get(firebase_uid=firebase_uid)

                # Set user on request
                request.user = user

                # Cache the authentication for faster subsequent requests
                request.session['cached_user_id'] = user.id
                request.session['auth_cache_expiry'] = time.time() + TOKEN_CACHE_DURATION

                return None  # Allow request to proceed

            except (auth.InvalidIdTokenError, auth.ExpiredIdTokenError) as e:
                logger.debug(f"Firebase token invalid/expired: {e}")
                self._clear_auth_cache(request)
                # Only redirect for protected paths
                if not is_public:
                    return redirect('/accounts/login/')
                return None

            except User.DoesNotExist as e:
                logger.debug(f"User not found for Firebase UID: {e}")
                self._clear_auth_cache(request)
                if not is_public:
                    return redirect('/accounts/login/')
                return None

            except Exception as e:
                logger.error(f"Firebase middleware error: {e}")
                self._clear_auth_cache(request)
                if not is_public:
                    return redirect('/accounts/login/')
                return None

        # No token found
        # For public paths, allow through (let the view handle it)
        if is_public:
            return None

        # For protected paths, redirect to login
        request.user = AnonymousUser()
        return redirect('/accounts/login/')

    def _clear_auth_cache(self, request):
        """Clear all authentication-related session data"""
        keys_to_clear = ['firebase_token', 'cached_user_id', 'auth_cache_expiry', 'user_id']
        for key in keys_to_clear:
            if key in request.session:
                del request.session[key]

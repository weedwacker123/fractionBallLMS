import time
import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, authenticate, login as auth_login, login
from django.contrib import messages
from django.conf import settings
from django.db import IntegrityError, DatabaseError
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from firebase_admin import auth

logger = logging.getLogger(__name__)
User = get_user_model()

# Token cache duration in seconds (5 minutes) - must match middleware
TOKEN_CACHE_DURATION = 300


def login_view(request):
    """
    Render the login page
    """
    # If user is already authenticated, redirect to home
    if request.user.is_authenticated:
        return redirect('/')
    
    return render(request, 'login.html')


def django_login_view(request):
    """
    Traditional Django login with username and password
    """
    if request.user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            logger.info(f"User {username} logged in successfully")
            messages.success(request, f'Welcome back, {user.get_full_name() or username}!')
            
            # Redirect to next page or home (with open redirect protection)
            next_url = request.GET.get('next', '/')
            if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                next_url = '/'
            return redirect(next_url)
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            messages.error(request, 'Invalid username or password. Please try again.')
    
    return render(request, 'django_login.html')


@csrf_exempt
@require_http_methods(["POST"])
def verify_token(request):
    """
    Verify Firebase token and create/update user session.
    CSRF exempt because authentication is done via Firebase token verification.
    """
    try:
        # Parse request body
        data = json.loads(request.body)
        token = data.get('token')
        
        if not token:
            return JsonResponse({'error': 'No token provided'}, status=400)
        
        # Verify Firebase token
        try:
            decoded_token = auth.verify_id_token(token)
            firebase_uid = decoded_token['uid']
            email = decoded_token.get('email', '')
            name = decoded_token.get('name', '')
            
            logger.info(f"Token verified for Firebase UID: {firebase_uid}, Email: {email}")
            
        except auth.InvalidIdTokenError:
            return JsonResponse({'error': 'Invalid Firebase token'}, status=401)
        except auth.ExpiredIdTokenError:
            return JsonResponse({'error': 'Expired Firebase token'}, status=401)
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return JsonResponse({'error': 'Token verification failed'}, status=401)
        
        # Try to get existing user
        try:
            user = User.objects.get(firebase_uid=firebase_uid)
            logger.info(f"Existing user found: {user.email}")

        except DatabaseError as e:
            logger.error(f"Database error during user lookup (firebase_uid={firebase_uid}): {e}", exc_info=True)
            return JsonResponse({
                'error': 'Database error during user lookup. Please try again later.'
            }, status=500)

        except User.DoesNotExist:
            # User doesn't exist - create a basic user for development
            # No school required for simplified local development

            # Parse name
            first_name = ''
            last_name = ''
            if name:
                name_parts = name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''

            # Create user
            username = email.split('@')[0] if email else f'user_{firebase_uid[:8]}'

            # Ensure unique username
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            try:
                user = User.objects.create(
                    firebase_uid=firebase_uid,
                    email=email,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    school=None,  # No school required for local development
                    role=User.Role.REGISTERED_USER,
                )
                logger.info(f"Created new user: {user.email} ({user.username})")
            except IntegrityError as e:
                # Race condition: user was created between our check and create
                logger.warning(f"IntegrityError during user creation, attempting to fetch existing user: {e}")
                try:
                    user = User.objects.get(firebase_uid=firebase_uid)
                    logger.info(f"Found existing user after race condition: {user.email}")
                except User.DoesNotExist:
                    logger.error(f"User creation failed and user not found: {e}")
                    return JsonResponse({
                        'error': 'Failed to create user account. Please try again.'
                    }, status=500)

        # Sync role FROM Firestore (single source of truth)
        try:
            from content.firestore_service import get_user_role
            from accounts.role_service import get_all_roles
            firestore_role = get_user_role(firebase_uid)

            if firestore_role:
                # Map legacy Firestore roles
                LEGACY_ROLE_MAP = {
                    'SCHOOL_ADMIN': 'REGISTERED_USER',
                    'TEACHER': 'REGISTERED_USER',
                }
                normalized_role = LEGACY_ROLE_MAP.get(firestore_role, firestore_role)

                # Validate against dynamically loaded roles
                known_roles = get_all_roles()
                if normalized_role in known_roles and user.role != normalized_role:
                    user.role = normalized_role
                    user.save(update_fields=['role'])
                    logger.info(f"Synced role from Firestore: {user.email} -> {normalized_role}"
                                + (f" (mapped from legacy '{firestore_role}')" if firestore_role != normalized_role else ""))
                elif normalized_role not in known_roles:
                    logger.warning(f"Unknown Firestore role '{firestore_role}' for user {user.email}; skipping role sync")
        except Exception as e:
            logger.warning(f"Failed to sync role from Firestore: {e}")
            # Non-blocking - continue with existing Django role

        # CRITICAL: Log the user in using Django's auth system
        # This sets _auth_user_id and _auth_user_backend in session
        # which makes @login_required and request.user.is_authenticated work
        try:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        except Exception as e:
            logger.error(f"Django login failed: {e}", exc_info=True)
            return JsonResponse({
                'error': 'Failed to establish session. Please try again.'
            }, status=500)

        # Store Firebase-specific data in session
        try:
            request.session['firebase_token'] = token
            request.session['user_id'] = user.id

            # Set auth cache for faster subsequent requests (must match middleware)
            request.session['cached_user_id'] = user.id
            request.session['auth_cache_expiry'] = time.time() + TOKEN_CACHE_DURATION

            # Set session to expire in 1 hour
            request.session.set_expiry(3600)
        except Exception as e:
            logger.error(f"Session setup failed: {e}", exc_info=True)
            return JsonResponse({
                'error': 'Failed to save session. Please try again.'
            }, status=500)

        # Sync user profile to Firestore (non-blocking)
        try:
            from content.firestore_service import create_or_update_user_profile
            create_or_update_user_profile(firebase_uid, {
                'email': user.email,
                'displayName': user.get_full_name(),
                'role': user.role,
                'school': user.school.name if user.school else None,
                'createdAt': user.created_at if hasattr(user, 'created_at') and user.created_at else None,
                'lastLogin': timezone.now()
            })
        except Exception as e:
            logger.warning(f"Failed to sync user profile to Firestore: {e}")
            # Non-blocking - don't fail login if Firestore sync fails

        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.get_full_name(),
                'role': user.role
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)
    except DatabaseError as e:
        logger.error(f"Database error during token verification: {e}", exc_info=True)
        return JsonResponse({
            'error': 'Database error. Please try again later.'
        }, status=500)
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}", exc_info=True)
        # In development, include more details; in production, keep generic
        error_message = f'Server error: {str(e)}' if settings.DEBUG else 'An unexpected error occurred. Please try again.'
        return JsonResponse({'error': error_message}, status=500)


GOOGLE_CLIENT_ID = '110595744029-9g3k1nbtko3jv7oupgb5aqri1jho5hcj.apps.googleusercontent.com'


@csrf_exempt
@require_http_methods(["POST"])
def google_auth(request):
    """
    Verify Google ID token from Google Identity Services and establish Django session.
    Bypasses Firebase client-side auth entirely — the Google ID token from GIS is
    verified server-side using google-auth, then a Django user is created/found.
    """
    try:
        data = json.loads(request.body)
        credential = data.get('credential')

        if not credential:
            return JsonResponse({'error': 'No credential provided'}, status=400)

        # Verify the Google ID token server-side
        try:
            from google.oauth2 import id_token
            from google.auth.transport import requests as google_requests

            idinfo = id_token.verify_oauth2_token(
                credential, google_requests.Request(), GOOGLE_CLIENT_ID
            )

            email = idinfo.get('email', '')
            name = idinfo.get('name', '')

            if not email:
                return JsonResponse({'error': 'No email in Google token'}, status=400)

            logger.info(f"Google ID token verified for email: {email}")

        except ValueError as e:
            logger.error(f"Invalid Google ID token: {e}")
            return JsonResponse({'error': 'Invalid Google token'}, status=401)

        # Find or create Firebase user to get firebase_uid
        try:
            firebase_user = auth.get_user_by_email(email)
            firebase_uid = firebase_user.uid
        except auth.UserNotFoundError:
            firebase_user = auth.create_user(email=email, display_name=name)
            firebase_uid = firebase_user.uid
            logger.info(f"Created new Firebase user for {email}: {firebase_uid}")
        except Exception as e:
            logger.error(f"Firebase user lookup/creation error: {e}")
            return JsonResponse({'error': 'Failed to process authentication'}, status=500)

        # Find or create Django user
        try:
            user = User.objects.get(firebase_uid=firebase_uid)
            logger.info(f"Existing Django user found: {user.email}")

        except DatabaseError as e:
            logger.error(f"Database error during user lookup: {e}", exc_info=True)
            return JsonResponse({'error': 'Database error. Please try again later.'}, status=500)

        except User.DoesNotExist:
            first_name = ''
            last_name = ''
            if name:
                name_parts = name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ''

            username = email.split('@')[0] if email else f'user_{firebase_uid[:8]}'
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1

            try:
                user = User.objects.create(
                    firebase_uid=firebase_uid,
                    email=email,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    school=None,
                    role=User.Role.REGISTERED_USER,
                )
                logger.info(f"Created new Django user: {user.email} ({user.username})")
            except IntegrityError as e:
                logger.warning(f"IntegrityError creating user, fetching existing: {e}")
                try:
                    user = User.objects.get(firebase_uid=firebase_uid)
                except User.DoesNotExist:
                    return JsonResponse({'error': 'Failed to create user account.'}, status=500)

        # Sync role from Firestore (non-blocking)
        try:
            from content.firestore_service import get_user_role
            from accounts.role_service import get_all_roles
            firestore_role = get_user_role(firebase_uid)
            if firestore_role:
                LEGACY_ROLE_MAP = {'SCHOOL_ADMIN': 'REGISTERED_USER', 'TEACHER': 'REGISTERED_USER'}
                normalized_role = LEGACY_ROLE_MAP.get(firestore_role, firestore_role)
                known_roles = get_all_roles()
                if normalized_role in known_roles and user.role != normalized_role:
                    user.role = normalized_role
                    user.save(update_fields=['role'])
        except Exception as e:
            logger.warning(f"Failed to sync role from Firestore: {e}")

        # Log user in via Django's auth system
        try:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        except Exception as e:
            logger.error(f"Django login failed: {e}", exc_info=True)
            return JsonResponse({'error': 'Failed to establish session.'}, status=500)

        # Set session cache for middleware
        try:
            request.session['user_id'] = user.id
            request.session['cached_user_id'] = user.id
            request.session['auth_cache_expiry'] = time.time() + TOKEN_CACHE_DURATION
            request.session.set_expiry(3600)
        except Exception as e:
            logger.error(f"Session setup failed: {e}", exc_info=True)
            return JsonResponse({'error': 'Failed to save session.'}, status=500)

        # Sync user profile to Firestore (non-blocking)
        try:
            from content.firestore_service import create_or_update_user_profile
            create_or_update_user_profile(firebase_uid, {
                'email': user.email,
                'displayName': user.get_full_name(),
                'role': user.role,
                'school': user.school.name if user.school else None,
                'lastLogin': timezone.now()
            })
        except Exception as e:
            logger.warning(f"Failed to sync user profile to Firestore: {e}")

        return JsonResponse({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.get_full_name(),
                'role': user.role
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error in google_auth: {e}", exc_info=True)
        error_message = f'Server error: {str(e)}' if settings.DEBUG else 'An unexpected error occurred.'
        return JsonResponse({'error': error_message}, status=500)


@require_http_methods(["POST", "GET"])
def logout_view(request):
    """
    Logout user by clearing session and all auth-related data
    """
    # Clear all session data (this clears firebase_token, cached_user_id, auth_cache_expiry, etc.)
    request.session.flush()

    # Clear Firebase token cookie
    response = redirect('/accounts/login/')
    response.delete_cookie('firebase_token')

    return response

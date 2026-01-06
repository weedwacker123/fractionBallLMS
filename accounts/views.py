import time
import json
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model, authenticate, login as auth_login, login
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.utils import timezone
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
            
            # Redirect to next page or home
            next_url = request.GET.get('next', '/')
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
            
            user = User.objects.create(
                firebase_uid=firebase_uid,
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                school=None,  # No school required for local development
                role=User.Role.TEACHER,
            )
            
            logger.info(f"Created new user: {user.email} ({user.username})")
        
        # CRITICAL: Log the user in using Django's auth system
        # This sets _auth_user_id and _auth_user_backend in session
        # which makes @login_required and request.user.is_authenticated work
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')

        # Store Firebase-specific data in session
        request.session['firebase_token'] = token
        request.session['user_id'] = user.id

        # Set auth cache for faster subsequent requests (must match middleware)
        request.session['cached_user_id'] = user.id
        request.session['auth_cache_expiry'] = time.time() + TOKEN_CACHE_DURATION

        # Set session to expire in 1 hour
        request.session.set_expiry(3600)

        # Sync user profile to Firestore (non-blocking)
        try:
            from content.firestore_service import create_or_update_user_profile
            create_or_update_user_profile(firebase_uid, {
                'email': user.email,
                'displayName': user.get_full_name(),
                'role': user.role,
                'school': user.school.name if user.school else None,
                'createdAt': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                'lastLogin': timezone.now().isoformat()
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
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Verify token error: {e}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


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

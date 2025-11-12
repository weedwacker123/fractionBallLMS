from django.shortcuts import render, redirect
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from firebase_admin import auth
import logging
import json

logger = logging.getLogger(__name__)
User = get_user_model()


def login_view(request):
    """
    Render the login page
    """
    # If user is already authenticated, redirect to home
    if request.user.is_authenticated:
        return redirect('/')
    
    return render(request, 'login.html')


@require_http_methods(["POST"])
def verify_token(request):
    """
    Verify Firebase token and create/update user session
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
        
        # Store token in session
        request.session['firebase_token'] = token
        request.session['user_id'] = user.id
        
        # Set session to expire in 1 hour
        request.session.set_expiry(3600)
        
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


def logout_view(request):
    """
    Logout user by clearing session
    """
    # Clear session
    request.session.flush()
    
    # Clear Firebase token cookie
    response = redirect('/accounts/login/')
    response.delete_cookie('firebase_token')
    
    return response

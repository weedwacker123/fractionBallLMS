"""
CMS Views for Fraction Ball Admin
A beautiful, user-friendly content management interface
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import ensure_csrf_cookie
from content.models import Activity, VideoAsset, Resource, Playlist
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


def has_cms_access(user):
    """Check whether user can access CMS via centralized RBAC."""
    if not user.is_authenticated:
        return False
    if getattr(user, 'is_superuser', False):
        return True
    return user.can('cms.access')


@ensure_csrf_cookie
def cms_login(request):
    """CMS Login view with beautiful UI"""
    logger.info(f"CMS Login - Method: {request.method}, User authenticated: {request.user.is_authenticated}")
    
    if request.user.is_authenticated:
        if has_cms_access(request.user):
            logger.info(f"User {request.user.username} already authenticated, redirecting to dashboard")
            return redirect('cms:dashboard')
        else:
            messages.error(request, 'You do not have permission to access the CMS.')
            return redirect('/')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        logger.info(f"CMS Login attempt for username: {username}")
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password.')
            return render(request, 'cms/login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            logger.info(f"User {username} authenticated successfully")
            if has_cms_access(user):
                login(request, user)
                logger.info(f"User {username} logged in successfully")
                messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
                
                # Get next URL or default to dashboard
                next_url = request.GET.get('next', '/cms/')
                return redirect(next_url)
            else:
                logger.warning(f"User {username} does not have CMS access permissions")
                messages.error(request, 'You do not have permission to access the CMS.')
        else:
            logger.warning(f"Failed login attempt for username: {username}")
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'cms/login.html')


@login_required(login_url='/cms/login/')
@user_passes_test(has_cms_access, login_url='/cms/login/')
def cms_dashboard(request):
    """CMS Dashboard with stats and quick actions"""
    
    # Get counts
    activity_count = Activity.objects.count()
    video_count = VideoAsset.objects.count()
    resource_count = Resource.objects.count()
    user_count = User.objects.count()
    
    # Get recent items
    recent_activities = Activity.objects.order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    
    context = {
        'activity_count': activity_count,
        'video_count': video_count,
        'resource_count': resource_count,
        'user_count': user_count,
        'recent_activities': recent_activities,
        'recent_users': recent_users,
    }
    
    return render(request, 'cms/dashboard.html', context)


def cms_logout(request):
    """Logout from CMS"""
    logout(request)
    messages.success(request, 'You have been signed out successfully.')
    return redirect('cms:login')

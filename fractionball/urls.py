"""
URL configuration for fractionball project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from api.views import home as api_home
from django.shortcuts import render
from config import views as config_views
from content.simple_upload_views import simple_upload_view, my_uploads_view, delete_video, delete_resource


def health_check(request):
    """Health check endpoint for Cloud Run and load balancers"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'fractionball-backend',
        'version': '1.0.0'
    })


def upload_view(request):
    return render(request, 'upload.html')

def library_view(request):
    return render(request, 'library.html')

def dashboard_view(request):
    return render(request, 'dashboard.html')

urlpatterns = [
    # Health check for Cloud Run
    path('health/', health_check, name='health-check'),
    
    # V4 Interface (Main public-facing site)
    path('', include('content.v4_urls')),
    
    # Authentication
    path('accounts/', include('accounts.urls')),
    
    # Legacy/Admin views
    path('api-home/', api_home, name='api-home'),
    
    # Upload UI (Simple - works without Firebase)
    path('upload/', simple_upload_view, name='simple-upload'),
    path('my-uploads/', my_uploads_view, name='my-uploads'),
    path('my-uploads/delete-video/<uuid:video_id>/', delete_video, name='delete-video'),
    path('my-uploads/delete-resource/<uuid:resource_id>/', delete_resource, name='delete-resource'),
    
    # Legacy upload UI
    path('upload-old/', upload_view, name='upload-old'),
    
    # Library UI (Legacy)
    path('library/', library_view, name='library-old'),
    
    # Dashboard UI (Teacher)
    path('dashboard/', dashboard_view, name='dashboard'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API
    path('api/', include('api.urls')),
    
    # Public configuration (no auth required)
    path('api/public-config/', config_views.public_config, name='public-config'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
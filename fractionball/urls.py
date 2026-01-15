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
from config import views as config_views
from content.page_views import custom_page


def health_check(request):
    """Health check endpoint for Cloud Run and load balancers"""
    return JsonResponse({
        'status': 'healthy',
        'service': 'fractionball-backend',
        'version': '1.0.0'
    })

urlpatterns = [
    # Health check for Cloud Run
    path('health/', health_check, name='health-check'),

    # V4 Interface (Main public-facing site)
    path('', include('content.v4_urls')),

    # Authentication
    path('accounts/', include('accounts.urls')),

    # Legacy/Admin views
    path('api-home/', api_home, name='api-home'),

    # Custom CMS Pages
    path('page/<slug:slug>/', custom_page, name='custom-page'),

    # CMS (Beautiful Admin Interface)
    path('cms/', include('content.cms_urls', namespace='cms')),

    # Django Admin
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
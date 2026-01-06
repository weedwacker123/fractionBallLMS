from django.urls import path, include
from rest_framework.routers import SimpleRouter
from . import views

# Use SimpleRouter (not DefaultRouter) to avoid duplicate format_suffix registration
router = SimpleRouter()
router.register(r'system', views.SystemConfigViewSet, basename='system-config')
router.register(r'features', views.FeatureFlagViewSet, basename='feature-flag')

urlpatterns = [
    # Public configuration
    path('public/', views.public_config, name='public-config'),
    
    # Config dashboard
    path('dashboard/', views.config_dashboard, name='config-dashboard'),
    
    # Include router URLs
    path('', include(router.urls)),
]











from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'schools', views.SchoolViewSet)
router.register(r'users', views.UserViewSet)

urlpatterns = [
    # Health check
    path('healthz/', views.health_check, name='health_check'),
    
    # User profile
    path('me/', views.MeView.as_view(), name='me'),
    
    # School-specific users
    path('schools/<int:school_id>/users/', views.SchoolUserListView.as_view(), name='school-users'),
    
    # Admin operations
    path('admin/', include('accounts.urls')),
    
    # System configuration
    path('config/', include('config.urls')),
    
    # Content management
    path('', include('content.urls')),
    
    # Include router URLs
    path('', include(router.urls)),
]

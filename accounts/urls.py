from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import admin_views

# Create router for admin ViewSets
router = DefaultRouter()
router.register(r'users', admin_views.AdminUserViewSet, basename='admin-user')
router.register(r'schools', admin_views.SchoolAdminViewSet, basename='admin-school')

urlpatterns = [
    # Admin dashboard
    path('dashboard/', admin_views.admin_dashboard, name='admin-dashboard'),
    
    # Include router URLs
    path('', include(router.urls)),
]

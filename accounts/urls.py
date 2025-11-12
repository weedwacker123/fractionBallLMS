from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import admin_views, views

# Create router for admin ViewSets
router = DefaultRouter()
router.register(r'users', admin_views.AdminUserViewSet, basename='admin-user')
router.register(r'schools', admin_views.SchoolAdminViewSet, basename='admin-school')

app_name = 'accounts'

urlpatterns = [
    # Authentication views
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-token/', views.verify_token, name='verify-token'),
    
    # Admin dashboard
    path('dashboard/', admin_views.admin_dashboard, name='admin-dashboard'),
    
    # Include router URLs
    path('', include(router.urls)),
]











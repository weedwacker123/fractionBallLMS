from django.urls import path, include
from rest_framework.routers import SimpleRouter
from . import admin_views, views

# Use SimpleRouter (not DefaultRouter) to avoid duplicate format_suffix registration
router = SimpleRouter()
router.register(r'users', admin_views.AdminUserViewSet, basename='admin-user')
router.register(r'schools', admin_views.SchoolAdminViewSet, basename='admin-school')

app_name = 'accounts'

urlpatterns = [
    # Authentication views
    path('login/', views.login_view, name='login'),  # Firebase login with Google SSO
    path('django-login/', views.django_login_view, name='django-login'),  # Plain username/password
    path('logout/', views.logout_view, name='logout'),
    path('verify-token/', views.verify_token, name='verify-token'),
    
    # Admin dashboard
    path('dashboard/', admin_views.admin_dashboard, name='admin-dashboard'),
    
    # Include router URLs
    path('', include(router.urls)),
]











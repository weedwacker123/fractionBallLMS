"""
Custom throttle classes for API rate limiting
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django.core.cache import cache


class AuthThrottle(UserRateThrottle):
    """Throttle for authentication endpoints"""
    scope = 'auth'


class LibraryThrottle(UserRateThrottle):
    """Throttle for library browsing endpoints"""
    scope = 'library'


class UploadThrottle(UserRateThrottle):
    """Throttle for upload endpoints"""
    scope = 'upload'


class AdminThrottle(UserRateThrottle):
    """Throttle for admin endpoints"""
    scope = 'admin'


class BurstThrottle(UserRateThrottle):
    """Short burst throttle for high-frequency operations"""
    scope = 'burst'
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class SchoolThrottle(UserRateThrottle):
    """Throttle based on school to prevent abuse from single schools"""
    
    def get_cache_key(self, request, view):
        if request.user.is_authenticated and hasattr(request.user, 'school') and request.user.school:
            ident = f"school_{request.user.school.id}"
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }


class CustomAnonThrottle(AnonRateThrottle):
    """Custom anonymous throttle with IP-based limiting"""
    
    def get_cache_key(self, request, view):
        # Use X-Forwarded-For header if available (for load balancers)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ident = x_forwarded_for.split(',')[0].strip()
        else:
            ident = self.get_ident(request)
        
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }

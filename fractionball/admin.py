"""
Custom Django Admin Site Configuration
Provides FireCMS-like experience for content management
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.utils.translation import gettext_lazy as _


class FractionBallAdminSite(AdminSite):
    """
    Custom admin site for Fraction Ball LMS
    Designed to provide FireCMS-like experience
    """
    
    # Site branding
    site_header = _('Fraction Ball CMS')
    site_title = _('Fraction Ball Admin')
    index_title = _('Content Management Dashboard')
    
    # Enable sidebar for FireCMS-like navigation
    enable_nav_sidebar = True
    
    def get_app_list(self, request, app_label=None):
        """
        Override to customize app ordering and grouping
        Similar to FireCMS collection groups
        """
        app_list = super().get_app_list(request, app_label)
        
        # Define custom ordering (FireCMS-like grouping)
        ordering = {
            'content': 1,      # Content Management (Activities, Videos, Resources)
            'accounts': 2,     # User Management
            'auth': 3,         # Authentication
            'admin': 4,        # Admin logs
        }
        
        # Sort apps by custom order
        app_list.sort(key=lambda x: ordering.get(x['app_label'], 99))
        
        return app_list


# Create custom admin site instance
admin_site = FractionBallAdminSite(name='fractionball_admin')

# Register models with custom admin site
# Note: Models are registered in their respective admin.py files
# This file provides the site configuration





















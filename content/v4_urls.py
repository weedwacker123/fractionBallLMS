"""
URL patterns for Fraction Ball V4 interface
"""
from django.urls import path
from . import v4_views

app_name = 'v4'

urlpatterns = [
    # Main pages
    path('', v4_views.home, name='home'),
    path('community/', v4_views.community, name='community'),
    path('faq/', v4_views.faq, name='faq'),
    
    # Activity pages
    path('activities/<slug:slug>/', v4_views.activity_detail, name='activity-detail'),
    
    # Search
    path('search/', v4_views.search_activities, name='search'),
    
    # User features
    path('notes/', v4_views.my_notes, name='my-notes'),
]










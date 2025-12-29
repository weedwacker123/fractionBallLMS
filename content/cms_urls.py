"""
CMS URL Configuration for Fraction Ball Admin
"""
from django.urls import path
from . import cms_views

app_name = 'cms'

urlpatterns = [
    path('', cms_views.cms_dashboard, name='dashboard'),
    path('login/', cms_views.cms_login, name='login'),
    path('logout/', cms_views.cms_logout, name='logout'),
]


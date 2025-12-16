"""
URL Configuration for file upload endpoints
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .upload_views import (
    FileUploadViewSet,
    get_streaming_url,
    get_resource_download_url
)

# Create router for ViewSet
router = DefaultRouter()
router.register(r'uploads', FileUploadViewSet, basename='file-upload')

urlpatterns = [
    # ViewSet routes (uploads/request-upload/, uploads/confirm-upload/, etc.)
    path('', include(router.urls)),
    
    # Video streaming URLs
    path('videos/<int:video_id>/stream/', get_streaming_url, name='video-stream'),
    
    # Resource download URLs
    path('resources/<int:resource_id>/download/', get_resource_download_url, name='resource-download'),
]













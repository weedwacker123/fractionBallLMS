from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'videos', views.VideoAssetViewSet, basename='videoasset')
router.register(r'resources', views.ResourceViewSet, basename='resource')
router.register(r'playlists', views.PlaylistViewSet, basename='playlist')

urlpatterns = [
    # Upload endpoints
    path('uploads/sign/', views.request_signed_upload_url, name='signed-upload-url'),
    path('uploads/complete/', views.upload_complete, name='upload-complete'),
    
    # Download endpoints
    path('resources/<uuid:resource_id>/download/', views.generate_resource_download_url, name='resource-download'),
    
    # Include router URLs
    path('', include(router.urls)),
]

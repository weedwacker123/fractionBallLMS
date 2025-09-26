from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, library_views, playlist_views, approval_views, bulk_views, reporting_views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'videos', views.VideoAssetViewSet, basename='videoasset')
router.register(r'resources', views.ResourceViewSet, basename='resource')
router.register(r'playlists', playlist_views.EnhancedPlaylistViewSet, basename='playlist')
router.register(r'approval/videos', approval_views.ContentApprovalViewSet, basename='approval-video')

urlpatterns = [
    # Library endpoints (public browsing)
    path('library/videos/', library_views.LibraryVideoListView.as_view(), name='library-videos'),
    path('library/videos/<uuid:pk>/', library_views.LibraryVideoDetailView.as_view(), name='library-video-detail'),
    path('library/resources/', library_views.LibraryResourceListView.as_view(), name='library-resources'),
    path('library/resources/<uuid:pk>/', library_views.LibraryResourceDetailView.as_view(), name='library-resource-detail'),
    path('library/playlists/', library_views.LibraryPlaylistListView.as_view(), name='library-playlists'),
    path('library/stats/', library_views.library_stats, name='library-stats'),
    
    # Dashboard
    path('dashboard/', library_views.teacher_dashboard, name='teacher-dashboard'),
    
    # Playlist sharing
    path('shared/<uuid:share_token>/', playlist_views.shared_playlist_view, name='shared-playlist'),
    path('shared/<uuid:share_token>/duplicate/', playlist_views.duplicate_shared_playlist, name='duplicate-shared-playlist'),
    
    # Analytics
    path('analytics/view/', playlist_views.track_video_view, name='track-video-view'),
    
    # Approval workflow
    path('approval/my-content-status/', approval_views.my_content_status, name='my-content-status'),
    
    # Bulk upload
    path('bulk/upload/', bulk_views.upload_csv, name='bulk-upload'),
    path('bulk/jobs/<uuid:job_id>/status/', bulk_views.job_status, name='bulk-job-status'),
    path('bulk/jobs/', bulk_views.my_upload_jobs, name='bulk-my-jobs'),
    path('bulk/jobs/school/', bulk_views.school_upload_jobs, name='bulk-school-jobs'),
    path('bulk/template/', bulk_views.download_template, name='bulk-template'),
    
    # Reporting
    path('reports/dashboard/', reporting_views.reports_dashboard, name='reports-dashboard'),
    path('reports/views/', reporting_views.export_views_report, name='export-views-report'),
    path('reports/downloads/', reporting_views.export_downloads_report, name='export-downloads-report'),
    path('reports/content/', reporting_views.export_content_report, name='export-content-report'),
    path('reports/analytics-summary/', reporting_views.export_analytics_summary, name='export-analytics-summary'),
    
    # Upload endpoints
    path('uploads/sign/', views.request_signed_upload_url, name='signed-upload-url'),
    path('uploads/complete/', views.upload_complete, name='upload-complete'),
    
    # Download endpoints
    path('resources/<uuid:resource_id>/download/', views.generate_resource_download_url, name='resource-download'),
    
    # Include router URLs (management endpoints)
    path('', include(router.urls)),
]

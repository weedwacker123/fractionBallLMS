"""
URL patterns for Fraction Ball V4 interface
"""
from django.urls import path
from . import v4_views, community_views, analytics_views, download_views, playlist_views

app_name = 'v4'

urlpatterns = [
    # Main pages
    path('', v4_views.home, name='home'),
    path('faq/', v4_views.faq, name='faq'),
    
    # Activity pages
    path('activities/<slug:slug>/', v4_views.activity_detail, name='activity-detail'),
    
    # Search
    path('search/', v4_views.search_activities, name='search'),
    
    # User features
    path('notes/', v4_views.my_notes, name='my-notes'),
    
    # Community Features
    path('community/', community_views.community_home, name='community'),
    path('community/create/', community_views.create_post, name='community-create'),
    path('community/post/<slug:slug>/', community_views.post_detail, name='community-post-detail'),
    path('community/post/<slug:post_slug>/comment/', community_views.add_comment, name='community-add-comment'),
    path('community/post/<uuid:post_id>/delete/', community_views.delete_post, name='community-delete-post'),
    path('community/post/<uuid:post_id>/edit/', community_views.edit_post, name='community-edit-post'),
    path('community/post/<uuid:post_id>/flag/', community_views.flag_post, name='community-flag-post'),
    path('community/comment/<uuid:comment_id>/delete/', community_views.delete_comment, name='community-delete-comment'),
    
    # Analytics
    path('analytics/', analytics_views.analytics_dashboard, name='analytics-dashboard'),
    path('analytics/video/<uuid:video_id>/', analytics_views.video_analytics, name='video-analytics'),
    path('analytics/export/', analytics_views.export_analytics_csv, name='analytics-export'),
    path('analytics/engagement-data/', analytics_views.activity_engagement_json, name='analytics-engagement-json'),
    
    # Download tracking
    path('download/resource/<uuid:resource_id>/', download_views.track_and_download_resource, name='download-resource'),
    
    # Playlist Management
    path('playlists/', playlist_views.my_playlists, name='my-playlists'),
    path('playlists/create/', playlist_views.create_playlist, name='create-playlist'),
    path('playlists/<uuid:playlist_id>/', playlist_views.playlist_detail, name='playlist-detail'),
    path('playlists/<uuid:playlist_id>/delete/', playlist_views.delete_playlist, name='delete-playlist'),
    path('playlists/<uuid:playlist_id>/duplicate/', playlist_views.duplicate_playlist, name='duplicate-playlist'),
    path('playlists/<uuid:playlist_id>/share/', playlist_views.create_share_link, name='create-share-link'),
    path('playlists/<uuid:playlist_id>/settings/', playlist_views.update_playlist_settings, name='update-playlist-settings'),
    path('playlists/shared/<uuid:share_token>/', playlist_views.view_shared_playlist, name='view-shared-playlist'),
    path('playlists/add/', playlist_views.add_to_playlist, name='add-to-playlist'),
    path('playlists/item/<uuid:item_id>/remove/', playlist_views.remove_from_playlist, name='remove-from-playlist'),
    path('playlists/json/', playlist_views.get_user_playlists_json, name='get-playlists-json'),
]





























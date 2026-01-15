"""
URL patterns for Fraction Ball V4 interface
"""
from django.urls import path
from . import v4_views, community_views, download_views

app_name = 'v4'

urlpatterns = [
    # Main pages (public)
    path('', v4_views.home, name='home'),
    path('faq/', v4_views.faq, name='faq'),

    # Activity pages (requires auth)
    path('activities/<slug:slug>/', v4_views.activity_detail, name='activity-detail'),

    # Search (public for homepage filtering)
    path('search/', v4_views.search_activities, name='search'),

    # User features (requires auth)
    path('notes/', v4_views.my_notes, name='my-notes'),

    # Community Features (requires auth)
    path('community/', community_views.community_home, name='community'),
    path('community/create/', community_views.create_post, name='community-create'),
    path('community/post/<slug:slug>/', community_views.post_detail, name='community-post-detail'),
    path('community/post/<slug:post_slug>/comment/', community_views.add_comment, name='community-add-comment'),
    path('community/post/<uuid:post_id>/delete/', community_views.delete_post, name='community-delete-post'),
    path('community/post/<uuid:post_id>/edit/', community_views.edit_post, name='community-edit-post'),
    path('community/post/<uuid:post_id>/flag/', community_views.flag_post, name='community-flag-post'),
    path('community/comment/<uuid:comment_id>/delete/', community_views.delete_comment, name='community-delete-comment'),

    # Download tracking
    path('download/resource/<uuid:resource_id>/', download_views.track_and_download_resource, name='download-resource'),
]





























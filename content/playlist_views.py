"""
Playlist management views for V4 interface
Allows teachers to create, manage, and share playlists of activities
"""
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone
from .models import Playlist, PlaylistItem, PlaylistShare, Activity, VideoAsset
import uuid

logger = logging.getLogger(__name__)


@login_required
def my_playlists(request):
    """
    View user's playlists
    """
    # Get user's own playlists
    my_playlists = Playlist.objects.filter(
        owner=request.user
    ).annotate(
        video_count=Count('playlistitem')
    ).order_by('-updated_at')
    
    # Get shared playlists (public playlists from same school)
    shared_playlists = Playlist.objects.filter(
        school=request.user.school,
        is_public=True
    ).exclude(
        owner=request.user
    ).annotate(
        video_count=Count('playlistitem')
    ).order_by('-updated_at')[:10]
    
    context = {
        'my_playlists': my_playlists,
        'shared_playlists': shared_playlists,
    }
    return render(request, 'playlists.html', context)


@login_required
def playlist_detail(request, playlist_id):
    """
    View details of a specific playlist
    """
    playlist = get_object_or_404(Playlist, id=playlist_id)
    
    # Check access permissions
    can_edit = playlist.owner == request.user
    can_view = (
        can_edit or 
        playlist.is_public or 
        (playlist.school == request.user.school)
    )
    
    if not can_view:
        return JsonResponse({
            'success': False,
            'message': 'You do not have permission to view this playlist'
        }, status=403)
    
    # Get playlist items with related data
    items = playlist.playlistitem_set.select_related(
        'video_asset'
    ).order_by('order')
    
    # Get activities linked to videos in playlist
    playlist_data = []
    for item in items:
        # Find activity associated with this video
        activity = Activity.objects.filter(
            video_asset=item.video_asset,
            is_published=True
        ).first()
        
        playlist_data.append({
            'item': item,
            'activity': activity,
        })
    
    # Get share links
    share_links = playlist.shares.filter(is_active=True).order_by('-created_at')
    
    context = {
        'playlist': playlist,
        'playlist_data': playlist_data,
        'can_edit': can_edit,
        'share_links': share_links,
    }
    return render(request, 'playlist_detail.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def create_playlist(request):
    """
    Create a new playlist
    """
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            is_public = request.POST.get('is_public') == 'on'
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'message': 'Playlist name is required'
                }, status=400)
            
            # Create playlist
            playlist = Playlist.objects.create(
                name=name,
                description=description,
                owner=request.user,
                school=request.user.school,
                is_public=is_public
            )
            
            logger.info(f"Playlist created: {playlist.id} by {request.user.username}")
            
            # If AJAX request, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': f'Playlist "{name}" created successfully',
                    'playlist_id': str(playlist.id),
                    'redirect_url': f'/playlists/{playlist.id}/'
                })
            
            return redirect('v4:playlist-detail', playlist_id=playlist.id)
            
        except Exception as e:
            logger.error(f"Failed to create playlist: {e}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'message': f'Failed to create playlist: {str(e)}'
                }, status=500)
            return redirect('v4:my-playlists')
    
    # GET - show form
    return render(request, 'playlist_create.html')


@login_required
@require_POST
def add_to_playlist(request):
    """
    Add an activity/video to a playlist
    """
    try:
        activity_id = request.POST.get('activity_id')
        playlist_id = request.POST.get('playlist_id')
        create_new = request.POST.get('create_new') == 'true'
        
        # Get or create playlist
        if create_new:
            playlist_name = request.POST.get('new_playlist_name', '').strip()
            if not playlist_name:
                return JsonResponse({
                    'success': False,
                    'message': 'Playlist name is required'
                }, status=400)
            
            playlist = Playlist.objects.create(
                name=playlist_name,
                owner=request.user,
                school=request.user.school,
                is_public=False
            )
            logger.info(f"New playlist created: {playlist.id}")
        else:
            playlist = get_object_or_404(Playlist, id=playlist_id, owner=request.user)
        
        # Get activity and its video
        activity = get_object_or_404(Activity, id=activity_id, is_published=True)
        
        if not activity.video_asset:
            return JsonResponse({
                'success': False,
                'message': 'This activity does not have a video'
            }, status=400)
        
        # Check if video already in playlist
        if PlaylistItem.objects.filter(
            playlist=playlist,
            video_asset=activity.video_asset
        ).exists():
            return JsonResponse({
                'success': False,
                'message': 'This video is already in the playlist'
            }, status=400)
        
        # Add to playlist (order will be auto-assigned)
        item = PlaylistItem.objects.create(
            playlist=playlist,
            video_asset=activity.video_asset,
            notes=f"From activity: {activity.title}"
        )
        
        logger.info(f"Added video {activity.video_asset.id} to playlist {playlist.id}")
        
        return JsonResponse({
            'success': True,
            'message': f'Added to playlist "{playlist.name}"',
            'playlist_id': str(playlist.id)
        })
        
    except Exception as e:
        logger.error(f"Failed to add to playlist: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to add to playlist: {str(e)}'
        }, status=500)


@login_required
@require_POST
def remove_from_playlist(request, item_id):
    """
    Remove an item from a playlist
    """
    try:
        item = get_object_or_404(PlaylistItem, id=item_id)
        
        # Check ownership
        if item.playlist.owner != request.user:
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to modify this playlist'
            }, status=403)
        
        playlist_id = item.playlist.id
        item.delete()
        
        logger.info(f"Removed item {item_id} from playlist {playlist_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from playlist'
        })
        
    except Exception as e:
        logger.error(f"Failed to remove from playlist: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to remove from playlist: {str(e)}'
        }, status=500)


@login_required
@require_POST
def delete_playlist(request, playlist_id):
    """
    Delete a playlist
    """
    try:
        playlist = get_object_or_404(Playlist, id=playlist_id, owner=request.user)
        
        playlist_name = playlist.name
        playlist.delete()
        
        logger.info(f"Playlist deleted: {playlist_id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f'Playlist "{playlist_name}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to delete playlist: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to delete playlist: {str(e)}'
        }, status=500)


@login_required
@require_POST
def duplicate_playlist(request, playlist_id):
    """
    Duplicate a playlist
    """
    try:
        original = get_object_or_404(Playlist, id=playlist_id)
        
        # Check if user can access the original
        can_access = (
            original.owner == request.user or
            original.is_public or
            (original.school == request.user.school)
        )
        
        if not can_access:
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to duplicate this playlist'
            }, status=403)
        
        # Create duplicate
        duplicate = Playlist.objects.create(
            name=f"{original.name} (Copy)",
            description=original.description,
            owner=request.user,
            school=request.user.school,
            is_public=False
        )
        
        # Copy all items
        items = original.playlistitem_set.all().order_by('order')
        for item in items:
            PlaylistItem.objects.create(
                playlist=duplicate,
                video_asset=item.video_asset,
                order=item.order,
                notes=item.notes
            )
        
        logger.info(f"Playlist duplicated: {playlist_id} -> {duplicate.id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f'Playlist "{original.name}" duplicated successfully',
            'playlist_id': str(duplicate.id),
            'redirect_url': f'/playlists/{duplicate.id}/'
        })
        
    except Exception as e:
        logger.error(f"Failed to duplicate playlist: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to duplicate playlist: {str(e)}'
        }, status=500)


@login_required
@require_POST
def create_share_link(request, playlist_id):
    """
    Create a shareable link for a playlist
    """
    try:
        playlist = get_object_or_404(Playlist, id=playlist_id, owner=request.user)
        
        # Get expiration days (optional)
        days = request.POST.get('expiration_days', '')
        expires_at = None
        if days and days.isdigit():
            expires_at = timezone.now() + timezone.timedelta(days=int(days))
        
        # Create share link
        share = PlaylistShare.objects.create(
            playlist=playlist,
            created_by=request.user,
            expires_at=expires_at,
            is_active=True
        )
        
        # Generate full URL
        share_url = request.build_absolute_uri(f'/playlists/shared/{share.share_token}/')
        
        logger.info(f"Share link created for playlist {playlist_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Share link created successfully',
            'share_url': share_url,
            'share_token': str(share.share_token)
        })
        
    except Exception as e:
        logger.error(f"Failed to create share link: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to create share link: {str(e)}'
        }, status=500)


@login_required
def view_shared_playlist(request, share_token):
    """
    View a playlist via share link
    """
    try:
        share = get_object_or_404(PlaylistShare, share_token=share_token, is_active=True)
        
        # Check if expired
        if share.is_expired:
            return render(request, 'playlist_expired.html', {
                'message': 'This share link has expired'
            })
        
        # Update access tracking
        share.view_count += 1
        share.last_accessed = timezone.now()
        share.save(update_fields=['view_count', 'last_accessed'])
        
        # Show playlist
        return playlist_detail(request, share.playlist.id)
        
    except Exception as e:
        logger.error(f"Failed to view shared playlist: {e}")
        return render(request, 'playlist_expired.html', {
            'message': 'Invalid or expired share link'
        })


@login_required
@require_POST
def update_playlist_settings(request, playlist_id):
    """
    Update playlist settings (name, description, visibility)
    """
    try:
        playlist = get_object_or_404(Playlist, id=playlist_id, owner=request.user)
        
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        is_public = request.POST.get('is_public') == 'on'
        
        if name:
            playlist.name = name
        if description is not None:
            playlist.description = description
        playlist.is_public = is_public
        playlist.save()
        
        logger.info(f"Playlist updated: {playlist_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'Playlist updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to update playlist: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to update playlist: {str(e)}'
        }, status=500)


@login_required
def get_user_playlists_json(request):
    """
    Get user's playlists as JSON (for AJAX dropdown)
    """
    playlists = Playlist.objects.filter(
        owner=request.user
    ).values('id', 'name', 'description').order_by('-updated_at')
    
    return JsonResponse({
        'playlists': list(playlists)
    })


# Alias for URL compatibility
shared_playlist_view = view_shared_playlist


def duplicate_shared_playlist(request, share_token):
    """
    Duplicate a playlist from a share link
    """
    try:
        share = get_object_or_404(PlaylistShare, share_token=share_token, is_active=True)
        
        # Check if expired
        if share.is_expired:
            return JsonResponse({
                'success': False,
                'message': 'This share link has expired'
            }, status=400)
        
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'message': 'You must be logged in to duplicate a playlist'
            }, status=401)
        
        original = share.playlist
        
        # Create duplicate
        duplicate = Playlist.objects.create(
            name=f"{original.name} (Copy)",
            description=original.description,
            owner=request.user,
            school=request.user.school,
            is_public=False
        )
        
        # Copy all items
        items = original.playlistitem_set.all().order_by('order')
        for item in items:
            PlaylistItem.objects.create(
                playlist=duplicate,
                video_asset=item.video_asset,
                order=item.order,
                notes=item.notes
            )
        
        logger.info(f"Shared playlist duplicated: {original.id} -> {duplicate.id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f'Playlist "{original.name}" duplicated successfully',
            'playlist_id': str(duplicate.id),
            'redirect_url': f'/playlists/{duplicate.id}/'
        })
        
    except Exception as e:
        logger.error(f"Failed to duplicate shared playlist: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to duplicate playlist: {str(e)}'
        }, status=500)


@require_POST
def track_video_view(request):
    """
    Track video view for analytics
    """
    try:
        video_id = request.POST.get('video_id')
        playlist_id = request.POST.get('playlist_id')
        
        # Tracking logic can be expanded here
        logger.info(f"Video view tracked: video={video_id}, playlist={playlist_id}")
        
        return JsonResponse({
            'success': True,
            'message': 'View tracked'
        })
        
    except Exception as e:
        logger.error(f"Failed to track video view: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to track view: {str(e)}'
        }, status=500)

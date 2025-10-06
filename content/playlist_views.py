"""
Enhanced playlist views with sharing, duplication, and reordering
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from datetime import timedelta
from accounts.permissions import IsTeacher
from .models import (
    Playlist, PlaylistItem, PlaylistShare, AuditLog, 
    AssetView, AssetDownload, VideoAsset, Resource
)
from .serializers import (
    PlaylistSerializer, PlaylistItemSerializer, 
    PlaylistShareSerializer, AuditLogSerializer
)
import logging
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()


class EnhancedPlaylistViewSet(ModelViewSet):
    """
    Enhanced playlist management with sharing and duplication
    """
    serializer_class = PlaylistSerializer
    permission_classes = [IsTeacher]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_public', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Playlists accessible to the user"""
        queryset = Playlist.objects.select_related(
            'owner', 'school'
        ).prefetch_related(
            'playlistitem_set__video_asset'
        ).filter(
            school=self.request.user.school
        )
        
        # Users can see their own playlists or public ones
        if not (self.request.user.is_admin or self.request.user.is_school_admin):
            queryset = queryset.filter(
                models.Q(owner=self.request.user) | models.Q(is_public=True)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """Set owner and school from request user"""
        serializer.save(
            owner=self.request.user,
            school=self.request.user.school
        )
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """
        Add a video to the playlist
        POST /api/playlists/{id}/add_item/
        """
        playlist = self.get_object()
        
        # Check ownership or admin permissions
        if not (
            playlist.owner == request.user or 
            request.user.is_admin or 
            request.user.is_school_admin
        ):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        video_id = request.data.get('video_id')
        notes = request.data.get('notes', '')
        order = request.data.get('order')
        
        if not video_id:
            return Response(
                {'error': 'video_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get video and verify access
            video = VideoAsset.objects.get(
                id=video_id,
                school=request.user.school,
                status='PUBLISHED'
            )
            
            # Check if video is already in playlist
            if PlaylistItem.objects.filter(playlist=playlist, video_asset=video).exists():
                return Response(
                    {'error': 'Video already in playlist'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create playlist item
            if order:
                # Insert at specific position, shift others
                PlaylistItem.objects.filter(
                    playlist=playlist, 
                    order__gte=order
                ).update(order=models.F('order') + 1)
            else:
                # Add at end
                last_item = PlaylistItem.objects.filter(playlist=playlist).order_by('-order').first()
                order = (last_item.order + 1) if last_item else 1
            
            playlist_item = PlaylistItem.objects.create(
                playlist=playlist,
                video_asset=video,
                order=order,
                notes=notes
            )
            
            # Log action
            AuditLog.objects.create(
                action='PLAYLIST_ITEM_ADDED',
                user=request.user,
                metadata={
                    'playlist_id': str(playlist.id),
                    'playlist_name': playlist.name,
                    'video_id': str(video.id),
                    'video_title': video.title,
                    'order': order
                },
                ip_address=self.get_client_ip(request)
            )
            
            serializer = PlaylistItemSerializer(playlist_item)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except VideoAsset.DoesNotExist:
            return Response(
                {'error': 'Video not found or not accessible'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Failed to add item to playlist {pk}: {e}")
            return Response(
                {'error': 'Failed to add item to playlist'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """
        Remove a video from the playlist
        DELETE /api/playlists/{id}/remove_item/
        """
        playlist = self.get_object()
        
        # Check ownership or admin permissions
        if not (
            playlist.owner == request.user or 
            request.user.is_admin or 
            request.user.is_school_admin
        ):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        item_id = request.data.get('item_id')
        if not item_id:
            return Response(
                {'error': 'item_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            playlist_item = PlaylistItem.objects.get(
                id=item_id,
                playlist=playlist
            )
            
            removed_order = playlist_item.order
            playlist_item.delete()
            
            # Reorder remaining items
            PlaylistItem.objects.filter(
                playlist=playlist,
                order__gt=removed_order
            ).update(order=models.F('order') - 1)
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except PlaylistItem.DoesNotExist:
            return Response(
                {'error': 'Playlist item not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['put'])
    def reorder(self, request, pk=None):
        """
        Reorder playlist items
        PUT /api/playlists/{id}/reorder/
        Body: {"item_orders": [{"id": "uuid", "order": 1}, ...]}
        """
        playlist = self.get_object()
        
        # Check ownership or admin permissions
        if not (
            playlist.owner == request.user or 
            request.user.is_admin or 
            request.user.is_school_admin
        ):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        item_orders = request.data.get('item_orders', [])
        if not item_orders:
            return Response(
                {'error': 'item_orders is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Update orders
                for item_order in item_orders:
                    item_id = item_order.get('id')
                    new_order = item_order.get('order')
                    
                    if not item_id or new_order is None:
                        continue
                    
                    PlaylistItem.objects.filter(
                        id=item_id,
                        playlist=playlist
                    ).update(order=new_order)
                
                # Log reorder action
                AuditLog.objects.create(
                    action='PLAYLIST_REORDERED',
                    user=request.user,
                    metadata={
                        'playlist_id': str(playlist.id),
                        'playlist_name': playlist.name,
                        'item_count': len(item_orders)
                    },
                    ip_address=self.get_client_ip(request)
                )
            
            return Response({'message': 'Playlist reordered successfully'})
            
        except Exception as e:
            logger.error(f"Failed to reorder playlist {pk}: {e}")
            return Response(
                {'error': 'Failed to reorder playlist'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """
        Create a share link for the playlist
        POST /api/playlists/{id}/share/
        """
        playlist = self.get_object()
        
        # Check ownership or admin permissions
        if not (
            playlist.owner == request.user or 
            request.user.is_admin or 
            request.user.is_school_admin
        ):
            return Response(
                {'error': 'Permission denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Optional expiration (in days)
        expires_in_days = request.data.get('expires_in_days')
        expires_at = None
        
        if expires_in_days:
            try:
                expires_in_days = int(expires_in_days)
                if expires_in_days > 0:
                    expires_at = timezone.now() + timedelta(days=expires_in_days)
            except (ValueError, TypeError):
                pass
        
        # Create share
        playlist_share = PlaylistShare.objects.create(
            playlist=playlist,
            created_by=request.user,
            expires_at=expires_at
        )
        
        # Log sharing action
        AuditLog.objects.create(
            action='PLAYLIST_SHARED',
            user=request.user,
            metadata={
                'playlist_id': str(playlist.id),
                'playlist_name': playlist.name,
                'share_token': str(playlist_share.share_token),
                'expires_at': expires_at.isoformat() if expires_at else None
            },
            ip_address=self.get_client_ip(request)
        )
        
        serializer = PlaylistShareSerializer(playlist_share)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Public access via token
def shared_playlist_view(request, share_token):
    """
    View a shared playlist (read-only)
    GET /api/shared/{token}/
    """
    try:
        # Get share by token
        playlist_share = get_object_or_404(
            PlaylistShare.objects.select_related(
                'playlist__owner', 'playlist__school'
            ).prefetch_related(
                'playlist__playlistitem_set__video_asset'
            ),
            share_token=share_token
        )
        
        # Check if share is valid
        if not playlist_share.is_valid:
            return Response(
                {'error': 'Share link is expired or inactive'}, 
                status=status.HTTP_410_GONE
            )
        
        # Update access tracking
        playlist_share.view_count += 1
        playlist_share.last_accessed = timezone.now()
        playlist_share.save(update_fields=['view_count', 'last_accessed'])
        
        # Return playlist data
        playlist_data = PlaylistSerializer(playlist_share.playlist).data
        playlist_data['is_shared'] = True
        playlist_data['shared_by'] = playlist_share.created_by.get_full_name()
        playlist_data['share_created_at'] = playlist_share.created_at
        
        return Response(playlist_data)
        
    except Exception as e:
        logger.error(f"Failed to load shared playlist {share_token}: {e}")
        return Response(
            {'error': 'Failed to load shared playlist'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsTeacher])
def duplicate_shared_playlist(request, share_token):
    """
    Duplicate a shared playlist to user's account
    POST /api/shared/{token}/duplicate/
    """
    try:
        # Get share by token
        playlist_share = get_object_or_404(
            PlaylistShare.objects.select_related(
                'playlist__owner', 'playlist__school'
            ).prefetch_related(
                'playlist__playlistitem_set__video_asset'
            ),
            share_token=share_token
        )
        
        # Check if share is valid
        if not playlist_share.is_valid:
            return Response(
                {'error': 'Share link is expired or inactive'}, 
                status=status.HTTP_410_GONE
            )
        
        original_playlist = playlist_share.playlist
        
        # Check if user already has a duplicate
        existing_duplicate = Playlist.objects.filter(
            owner=request.user,
            name=f"{original_playlist.name} (Copy)"
        ).first()
        
        if existing_duplicate:
            return Response(
                {'error': 'You already have a copy of this playlist'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Create new playlist
            new_playlist = Playlist.objects.create(
                name=f"{original_playlist.name} (Copy)",
                description=f"Duplicated from {original_playlist.owner.get_full_name()}'s playlist.\n\n{original_playlist.description}",
                owner=request.user,
                school=request.user.school,
                is_public=False  # Duplicates are private by default
            )
            
            # Copy playlist items (only videos accessible to user's school)
            items_to_create = []
            accessible_videos = VideoAsset.objects.filter(
                school=request.user.school,
                status='PUBLISHED'
            ).values_list('id', flat=True)
            
            for item in original_playlist.playlistitem_set.all():
                if item.video_asset.id in accessible_videos:
                    items_to_create.append(PlaylistItem(
                        playlist=new_playlist,
                        video_asset=item.video_asset,
                        order=item.order,
                        notes=item.notes
                    ))
            
            PlaylistItem.objects.bulk_create(items_to_create)
            
            # Log duplication action
            AuditLog.objects.create(
                action='PLAYLIST_DUPLICATED',
                user=request.user,
                metadata={
                    'original_playlist_id': str(original_playlist.id),
                    'original_playlist_name': original_playlist.name,
                    'original_owner': original_playlist.owner.get_full_name(),
                    'new_playlist_id': str(new_playlist.id),
                    'new_playlist_name': new_playlist.name,
                    'items_copied': len(items_to_create),
                    'share_token': str(share_token)
                },
                ip_address=get_client_ip(request)
            )
        
        # Return new playlist
        serializer = PlaylistSerializer(new_playlist)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Failed to duplicate shared playlist {share_token}: {e}")
        return Response(
            {'error': 'Failed to duplicate playlist'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsTeacher])
def track_video_view(request):
    """
    Track video view for analytics
    POST /api/analytics/view/
    """
    try:
        video_id = request.data.get('video_id')
        session_id = request.data.get('session_id', str(uuid.uuid4()))
        duration_watched = request.data.get('duration_watched')
        completion_percentage = request.data.get('completion_percentage')
        referrer = request.data.get('referrer', '')
        
        if not video_id:
            return Response(
                {'error': 'video_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get video and verify access
        video = VideoAsset.objects.get(
            id=video_id,
            school=request.user.school
        )
        
        # Check for duplicate view (same session)
        existing_view = AssetView.objects.filter(
            asset=video,
            user=request.user,
            session_id=session_id
        ).first()
        
        if existing_view:
            # Update existing view with new data
            if duration_watched is not None:
                existing_view.duration_watched = max(
                    existing_view.duration_watched or 0, 
                    duration_watched
                )
            if completion_percentage is not None:
                existing_view.completion_percentage = max(
                    existing_view.completion_percentage or 0.0, 
                    completion_percentage
                )
            existing_view.save()
            view_record = existing_view
        else:
            # Create new view record
            view_record = AssetView.objects.create(
                asset=video,
                user=request.user,
                session_id=session_id,
                duration_watched=duration_watched,
                completion_percentage=completion_percentage,
                referrer=referrer
            )
        
        # Log view action
        AuditLog.objects.create(
            action='VIDEO_VIEWED',
            user=request.user,
            metadata={
                'video_id': str(video.id),
                'video_title': video.title,
                'duration_watched': duration_watched,
                'completion_percentage': completion_percentage,
                'session_id': session_id
            },
            ip_address=get_client_ip(request)
        )
        
        return Response({
            'message': 'View tracked successfully',
            'view_id': str(view_record.id)
        })
        
    except VideoAsset.DoesNotExist:
        return Response(
            {'error': 'Video not found or not accessible'}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Failed to track video view: {e}")
        return Response(
            {'error': 'Failed to track view'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip







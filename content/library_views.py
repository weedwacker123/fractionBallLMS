"""
Library views for content discovery and teacher dashboard
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from accounts.permissions import require_permission
from .models import VideoAsset, Resource, Playlist
from .serializers import VideoAssetSerializer, ResourceSerializer, PlaylistSerializer
from .filters import VideoAssetFilter, ResourceFilter
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class LibraryPagination(PageNumberPagination):
    """Custom pagination for library views"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class LibraryVideoListView(generics.ListAPIView):
    """
    Library view for videos with advanced search, filtering, and pagination
    GET /api/library/videos/
    """
    serializer_class = VideoAssetSerializer
    permission_classes = [require_permission('activities_view')]
    pagination_class = LibraryPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = VideoAssetFilter
    
    def get_queryset(self):
        """Optimized queryset for library browsing"""
        queryset = VideoAsset.objects.select_related(
            'owner', 'school', 'reviewed_by'
        ).filter(
            # Only published videos visible in library (except to owners/admins)
            school=self.request.user.school
        )
        
        # Non-owners can only see published videos (unless they're admins)
        if not self.request.user.can('cms_edit'):
            queryset = queryset.filter(
                Q(owner=self.request.user) | Q(status='PUBLISHED')
            )
        
        return queryset.distinct()
    
    def get_filterset_kwargs(self, filterset_class):
        """Pass request to filterset for dynamic owner choices"""
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['request'] = self.request
        return kwargs
    
    def list(self, request, *args, **kwargs):
        """Enhanced list response with metadata"""
        response = super().list(request, *args, **kwargs)
        
        # Add search/filter metadata
        queryset = self.filter_queryset(self.get_queryset())
        
        response.data['filters'] = {
            'total_results': queryset.count(),
            'grades_available': list(
                queryset.values_list('grade', flat=True).distinct().order_by('grade')
            ),
            'topics_available': list(
                queryset.values_list('topic', flat=True).distinct().order_by('topic')
            ),
            'applied_filters': dict(request.query_params)
        }
        
        return response


class LibraryResourceListView(generics.ListAPIView):
    """
    Library view for resources with search and filtering
    GET /api/library/resources/
    """
    serializer_class = ResourceSerializer
    permission_classes = [require_permission('resources_download')]
    pagination_class = LibraryPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = ResourceFilter
    
    def get_queryset(self):
        """Optimized queryset for resource browsing"""
        queryset = Resource.objects.select_related(
            'owner', 'school'
        ).filter(
            school=self.request.user.school
        )
        
        # Non-owners can only see published resources
        if not self.request.user.can('cms_edit'):
            queryset = queryset.filter(
                Q(owner=self.request.user) | Q(status='PUBLISHED')
            )
        
        return queryset.distinct()
    
    def get_filterset_kwargs(self, filterset_class):
        """Pass request to filterset for dynamic owner choices"""
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['request'] = self.request
        return kwargs


class LibraryPlaylistListView(generics.ListAPIView):
    """
    Library view for playlists
    GET /api/library/playlists/
    """
    serializer_class = PlaylistSerializer
    permission_classes = [require_permission('activities_view')]
    pagination_class = LibraryPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_public', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Playlists visible to the user"""
        queryset = Playlist.objects.select_related(
            'owner', 'school'
        ).prefetch_related(
            'playlistitem_set__video_asset'
        ).filter(
            school=self.request.user.school
        )
        
        # Users can see their own playlists or public ones
        if not self.request.user.can('cms_edit'):
            queryset = queryset.filter(
                Q(owner=self.request.user) | Q(is_public=True)
            )
        
        return queryset


class LibraryVideoDetailView(generics.RetrieveAPIView):
    """
    Detailed view of a video asset
    GET /api/library/videos/{id}/
    """
    serializer_class = VideoAssetSerializer
    permission_classes = [require_permission('activities_view')]
    
    def get_queryset(self):
        """Videos accessible to the user"""
        return VideoAsset.objects.select_related(
            'owner', 'school', 'reviewed_by'
        ).filter(
            school=self.request.user.school
        )
    
    def get_object(self):
        """Get video with permission check"""
        video = super().get_object()
        
        # Check if user can access this video
        if not self.request.user.can('activity_view', obj=video):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to view this video.")
        
        return video


class LibraryResourceDetailView(generics.RetrieveAPIView):
    """
    Detailed view of a resource
    GET /api/library/resources/{id}/
    """
    serializer_class = ResourceSerializer
    permission_classes = [require_permission('resources_download')]
    
    def get_queryset(self):
        """Resources accessible to the user"""
        return Resource.objects.select_related(
            'owner', 'school'
        ).filter(
            school=self.request.user.school
        )
    
    def get_object(self):
        """Get resource with permission check"""
        resource = super().get_object()
        
        # Check if user can access this resource
        if not self.request.user.can('resource_download', obj=resource):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to view this resource.")
        
        return resource


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def teacher_dashboard(request):
    """
    Teacher dashboard with recent uploads, stats, and quick links
    GET /api/dashboard/
    """
    try:
        user = request.user
        school = user.school
        if not school:
            return Response(
                {'error': 'User is not assigned to a school'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate date ranges
        now = timezone.now()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # Recent uploads by user (last 5)
        recent_uploads = VideoAsset.objects.filter(
            owner=user
        ).select_related('school').order_by('-created_at')[:5]
        
        recent_uploads_data = VideoAssetSerializer(recent_uploads, many=True).data
        
        # User's playlists with video counts
        my_playlists = Playlist.objects.filter(
            owner=user
        ).annotate(
            video_count=Count('playlistitem')
        ).order_by('-updated_at')[:5]
        
        my_playlists_data = []
        for playlist in my_playlists:
            playlist_data = PlaylistSerializer(playlist).data
            playlist_data['video_count'] = playlist.video_count
            my_playlists_data.append(playlist_data)
        
        # School statistics
        school_videos = VideoAsset.objects.filter(school=school, status='PUBLISHED')
        school_resources = Resource.objects.filter(school=school, status='PUBLISHED')
        
        school_stats = {
            'total_videos': school_videos.count(),
            'total_resources': school_resources.count(),
            'total_playlists': Playlist.objects.filter(school=school, is_public=True).count(),
            'videos_this_week': school_videos.filter(created_at__gte=week_ago).count(),
            'videos_this_month': school_videos.filter(created_at__gte=month_ago).count(),
        }
        
        # User's personal stats
        user_stats = {
            'my_videos': VideoAsset.objects.filter(owner=user).count(),
            'my_resources': Resource.objects.filter(owner=user).count(),
            'my_playlists': Playlist.objects.filter(owner=user).count(),
            'videos_uploaded_this_week': VideoAsset.objects.filter(
                owner=user, created_at__gte=week_ago
            ).count(),
        }
        
        # Popular content in school (most viewed/accessed)
        popular_videos = school_videos.annotate(
            # This would typically use view counts from analytics
            # For now, we'll use creation date as a proxy
            popularity_score=Count('playlistitem')
        ).order_by('-popularity_score', '-created_at')[:5]
        
        popular_videos_data = VideoAssetSerializer(popular_videos, many=True).data
        
        # Recent activity in school
        recent_school_videos = school_videos.order_by('-created_at')[:5]
        recent_school_videos_data = VideoAssetSerializer(recent_school_videos, many=True).data
        
        # Quick links based on user's activity
        quick_links = []
        
        # Add grade-specific links based on user's content
        user_grades = VideoAsset.objects.filter(
            owner=user
        ).values_list('grade', flat=True).distinct()
        
        for grade in user_grades[:3]:  # Top 3 grades
            if grade:
                quick_links.append({
                    'title': f'Grade {grade} Videos',
                    'url': f'/api/library/videos/?grade={grade}',
                    'description': f'Browse all Grade {grade} content'
                })
        
        # Add topic-specific links
        user_topics = VideoAsset.objects.filter(
            owner=user
        ).values_list('topic', flat=True).distinct()
        
        for topic in user_topics[:2]:  # Top 2 topics
            if topic:
                from .models import TOPIC_CHOICES
                topic_display = dict(TOPIC_CHOICES).get(topic, topic)
                quick_links.append({
                    'title': topic_display,
                    'url': f'/api/library/videos/?topic={topic}',
                    'description': f'Explore {topic_display} resources'
                })
        
        # Compile dashboard data
        dashboard_data = {
            'user_info': {
                'name': user.get_full_name(),
                'role': user.get_role_display(),
                'school': school.name,
            },
            'recent_uploads': recent_uploads_data,
            'my_playlists': my_playlists_data,
            'school_stats': school_stats,
            'user_stats': user_stats,
            'popular_content': popular_videos_data,
            'recent_school_content': recent_school_videos_data,
            'quick_links': quick_links,
            'generated_at': now.isoformat(),
        }
        
        logger.info(f"Generated dashboard for user {user.id}")
        
        return Response(dashboard_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Dashboard generation failed for user {request.user.id}: {e}")
        return Response(
            {'error': 'Failed to generate dashboard', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def library_stats(request):
    """
    Library statistics and metadata
    GET /api/library/stats/
    """
    try:
        user = request.user
        school = user.school
        if not school:
            return Response(
                {'error': 'User is not assigned to a school'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get published content counts by category
        videos_by_grade = VideoAsset.objects.filter(
            school=school, status='PUBLISHED'
        ).values('grade').annotate(count=Count('id')).order_by('grade')
        
        videos_by_topic = VideoAsset.objects.filter(
            school=school, status='PUBLISHED'
        ).values('topic').annotate(count=Count('id')).order_by('topic')
        
        resources_by_type = Resource.objects.filter(
            school=school, status='PUBLISHED'
        ).values('file_type').annotate(count=Count('id')).order_by('file_type')
        
        # Most active users
        active_teachers = User.objects.filter(
            school=school,
            role__in=['REGISTERED_USER', 'CONTENT_MANAGER', 'ADMIN']
        ).annotate(
            video_count=Count('videoasset', filter=Q(videoasset__status='PUBLISHED')),
            resource_count=Count('resource', filter=Q(resource__status='PUBLISHED'))
        ).filter(
            models.Q(video_count__gt=0) | models.Q(resource_count__gt=0)
        ).order_by('-video_count', '-resource_count')[:10]
        
        active_teachers_data = []
        for teacher in active_teachers:
            active_teachers_data.append({
                'name': teacher.get_full_name(),
                'video_count': teacher.video_count,
                'resource_count': teacher.resource_count,
                'total_content': teacher.video_count + teacher.resource_count
            })
        
        stats_data = {
            'videos_by_grade': list(videos_by_grade),
            'videos_by_topic': list(videos_by_topic),
            'resources_by_type': list(resources_by_type),
            'active_teachers': active_teachers_data,
            'total_published_videos': VideoAsset.objects.filter(
                school=school, status='PUBLISHED'
            ).count(),
            'total_published_resources': Resource.objects.filter(
                school=school, status='PUBLISHED'
            ).count(),
            'total_public_playlists': Playlist.objects.filter(
                school=school, is_public=True
            ).count(),
        }
        
        return Response(stats_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Library stats failed for user {request.user.id}: {e}")
        return Response(
            {'error': 'Failed to generate library stats', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db import models
from accounts.permissions import IsTeacher, IsOwnerOrSchoolAdmin
from .models import VideoAsset, Resource, Playlist, PlaylistItem
from .serializers import (
    VideoAssetSerializer, VideoAssetCreateSerializer,
    ResourceSerializer, ResourceCreateSerializer,
    PlaylistSerializer, PlaylistItemSerializer,
    SignedUploadRequestSerializer, SignedUploadResponseSerializer,
    UploadCompleteSerializer
)
from .services import firebase_storage
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class VideoAssetViewSet(ModelViewSet):
    """
    ViewSet for VideoAsset management
    """
    serializer_class = VideoAssetSerializer
    permission_classes = [IsTeacher]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['grade', 'topic', 'status', 'owner']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['title', 'created_at', 'duration']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter videos based on user's school and permissions"""
        queryset = VideoAsset.objects.select_related('owner', 'school').all()
        
        # Users can only see videos from their school
        queryset = queryset.filter(school=self.request.user.school)
        
        # Non-owners can only see published videos (unless they're admins)
        if not (self.request.user.is_admin or self.request.user.is_school_admin):
            queryset = queryset.filter(
                models.Q(owner=self.request.user) | 
                models.Q(status='PUBLISHED')
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.action == 'create':
            return VideoAssetCreateSerializer
        return VideoAssetSerializer
    
    def perform_create(self, serializer):
        """Set owner and school from request user"""
        serializer.save(
            owner=self.request.user,
            school=self.request.user.school
        )


class ResourceViewSet(ModelViewSet):
    """
    ViewSet for Resource management
    """
    serializer_class = ResourceSerializer
    permission_classes = [IsTeacher]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['file_type', 'grade', 'topic', 'status', 'owner']
    search_fields = ['title', 'description', 'tags']
    ordering_fields = ['title', 'created_at', 'file_size']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter resources based on user's school and permissions"""
        queryset = Resource.objects.select_related('owner', 'school').all()
        
        # Users can only see resources from their school
        queryset = queryset.filter(school=self.request.user.school)
        
        # Non-owners can only see published resources (unless they're admins)
        if not (self.request.user.is_admin or self.request.user.is_school_admin):
            queryset = queryset.filter(
                models.Q(owner=self.request.user) | 
                models.Q(status='PUBLISHED')
            )
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.action == 'create':
            return ResourceCreateSerializer
        return ResourceSerializer


class PlaylistViewSet(ModelViewSet):
    """
    ViewSet for Playlist management
    """
    serializer_class = PlaylistSerializer
    permission_classes = [IsTeacher]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_public', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-updated_at']
    
    def get_queryset(self):
        """Filter playlists based on user's school and visibility"""
        queryset = Playlist.objects.select_related('owner', 'school').prefetch_related(
            'playlistitem_set__video_asset'
        ).all()
        
        # Users can only see playlists from their school
        queryset = queryset.filter(school=self.request.user.school)
        
        # Users can see their own playlists or public ones
        if not (self.request.user.is_admin or self.request.user.is_school_admin):
            queryset = queryset.filter(
                models.Q(owner=self.request.user) | 
                models.Q(is_public=True)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        """Set owner and school from request user"""
        serializer.save(
            owner=self.request.user,
            school=self.request.user.school
        )


@api_view(['POST'])
@permission_classes([IsTeacher])
def request_signed_upload_url(request):
    """
    Generate signed URL for direct upload to Firebase Storage
    POST /api/uploads/sign/
    """
    serializer = SignedUploadRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Extract validated data
        filename = serializer.validated_data['filename']
        file_size = serializer.validated_data['file_size']
        content_type = serializer.validated_data['content_type']
        category = serializer.validated_data['category']
        
        # Generate signed upload URL
        upload_data = firebase_storage.generate_upload_url(
            filename=filename,
            file_size=file_size,
            content_type=content_type,
            file_category=category,
            user_id=request.user.id,
            school_id=request.user.school.id
        )
        
        # Return upload URL and metadata
        response_serializer = SignedUploadResponseSerializer(upload_data)
        
        logger.info(
            f"Generated signed upload URL for user {request.user.id}: "
            f"{filename} ({file_size} bytes, {category})"
        )
        
        return Response(response_serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Failed to generate signed upload URL: {e}")
        return Response(
            {'error': 'Failed to generate upload URL', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsTeacher])
def upload_complete(request):
    """
    Handle upload completion and create asset record
    POST /api/uploads/complete/
    """
    serializer = UploadCompleteSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid completion data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        storage_path = serializer.validated_data['storage_path']
        
        # Verify file exists in Firebase Storage
        file_metadata = firebase_storage.get_file_metadata(storage_path)
        if not file_metadata:
            return Response(
                {'error': 'File not found in storage'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Determine if it's a video or resource based on storage path
        is_video = storage_path.startswith('videos/')
        
        # Create asset record
        if is_video:
            asset = VideoAsset.objects.create(
                title=serializer.validated_data['title'],
                description=serializer.validated_data.get('description', ''),
                grade=serializer.validated_data.get('grade', ''),
                topic=serializer.validated_data.get('topic', ''),
                tags=serializer.validated_data.get('tags', []),
                duration=serializer.validated_data.get('duration'),
                file_size=file_metadata.get('size'),
                storage_uri=firebase_storage.get_public_url(storage_path),
                owner=request.user,
                school=request.user.school,
                status='DRAFT'
            )
            serializer_class = VideoAssetSerializer
        else:
            # Determine file type from content type or extension
            content_type = file_metadata.get('content_type', '')
            file_type = 'other'
            if 'pdf' in content_type:
                file_type = 'pdf'
            elif 'word' in content_type or 'msword' in content_type:
                file_type = 'doc' if 'msword' in content_type else 'docx'
            elif 'powerpoint' in content_type or 'presentation' in content_type:
                file_type = 'ppt' if 'powerpoint' in content_type else 'pptx'
            elif 'excel' in content_type or 'spreadsheet' in content_type:
                file_type = 'xls' if 'excel' in content_type else 'xlsx'
            elif 'text' in content_type:
                file_type = 'txt'
            elif 'image' in content_type:
                file_type = 'image'
            
            asset = Resource.objects.create(
                title=serializer.validated_data['title'],
                description=serializer.validated_data.get('description', ''),
                file_uri=firebase_storage.get_public_url(storage_path),
                file_type=file_type,
                file_size=file_metadata.get('size'),
                grade=serializer.validated_data.get('grade', ''),
                topic=serializer.validated_data.get('topic', ''),
                tags=serializer.validated_data.get('tags', []),
                owner=request.user,
                school=request.user.school,
                status='DRAFT'
            )
            serializer_class = ResourceSerializer
        
        # Return created asset
        response_serializer = serializer_class(asset)
        
        logger.info(
            f"Created {asset.__class__.__name__} {asset.id} for user {request.user.id}"
        )
        
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Failed to complete upload: {e}")
        return Response(
            {'error': 'Failed to complete upload', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsTeacher])
def generate_resource_download_url(request, resource_id):
    """
    Generate signed download URL for a resource (not videos)
    POST /api/resources/{id}/download/
    """
    try:
        # Get resource and check permissions
        resource = Resource.objects.get(
            id=resource_id,
            school=request.user.school
        )
        
        # Check if user can access this resource
        if not (
            resource.owner == request.user or 
            resource.status == 'PUBLISHED' or
            request.user.is_admin or 
            request.user.is_school_admin
        ):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Extract storage path from file URI
        # This is a simplified extraction - in production, store the path separately
        storage_path = resource.file_uri.split('/o/')[-1].split('?')[0].replace('%2F', '/')
        
        # Generate signed download URL
        download_url = firebase_storage.generate_download_url(
            storage_path=storage_path,
            expires_in_hours=24
        )
        
        logger.info(
            f"Generated download URL for resource {resource_id} by user {request.user.id}"
        )
        
        return Response({
            'download_url': download_url,
            'expires_in_hours': 24,
            'filename': resource.title
        })
        
    except Resource.DoesNotExist:
        return Response(
            {'error': 'Resource not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Failed to generate download URL: {e}")
        return Response(
            {'error': 'Failed to generate download URL', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
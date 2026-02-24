"""
Upload views for Firebase Storage integration
Provides endpoints for generating upload URLs and managing file uploads
"""

import logging
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

from accounts.permissions import require_permission
from .firebase_storage import get_storage_service
from .models import VideoAsset, Resource
from .serializers import VideoAssetSerializer, ResourceSerializer
from .file_validators import validate_and_check_limits

logger = logging.getLogger(__name__)


class FileUploadViewSet(viewsets.ViewSet):
    """
    ViewSet for file upload operations using Firebase Storage
    """
    permission_classes = [require_permission('cms_edit')]
    
    @action(detail=False, methods=['post'], url_path='request-upload')
    def request_upload(self, request):
        """
        Generate a signed upload URL for client-side file upload
        
        POST /api/content/uploads/request-upload/
        Body:
        {
            "file_type": "video",  // or "resource", "thumbnail", "lesson"
            "content_type": "video/mp4",
            "file_size": 52428800,
            "file_name": "my-video.mp4"
        }
        
        Returns:
        {
            "upload_url": "https://storage.googleapis.com/...",
            "file_path": "videos/20250118/abc123.mp4",
            "file_id": "temp-abc123",
            "expires_in": 3600
        }
        """
        try:
            # Validate request data
            file_type = request.data.get('file_type')
            content_type = request.data.get('content_type')
            file_size = request.data.get('file_size')
            file_name = request.data.get('file_name', 'upload')
            
            if not all([file_type, content_type, file_size]):
                return Response(
                    {'error': 'Missing required fields: file_type, content_type, file_size'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate file size is an integer
            try:
                file_size = int(file_size)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'file_size must be an integer'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Comprehensive validation and rate limiting
            is_valid, error_msg = validate_and_check_limits(
                user_id=request.user.id,
                file_type=file_type,
                content_type=content_type,
                file_size=file_size,
                file_name=file_name
            )
            
            if not is_valid:
                return Response(
                    {'error': error_msg},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get storage service
            storage_service = get_storage_service()
            
            # Generate upload URL
            upload_url, file_path = storage_service.generate_upload_url(
                file_type=file_type,
                content_type=content_type,
                file_size=file_size,
                user_id=request.user.id
            )
            
            # Extract file ID from path for tracking
            file_id = file_path.split('/')[-1].split('.')[0]
            
            logger.info(
                f"Upload URL generated for user {request.user.id}: "
                f"{file_type} - {file_path}"
            )
            
            return Response({
                'upload_url': upload_url,
                'file_path': file_path,
                'file_id': f"temp-{file_id}",
                'expires_in': 3600,  # 1 hour
                'instructions': {
                    'method': 'PUT',
                    'headers': {
                        'Content-Type': content_type,
                    }
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Error generating upload URL: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to generate upload URL'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='confirm-upload')
    def confirm_upload(self, request):
        """
        Confirm that a file upload was successful and create database record
        
        POST /api/content/uploads/confirm-upload/
        Body:
        {
            "file_path": "videos/20250118/abc123.mp4",
            "file_type": "video",
            "title": "My Video",
            "description": "Video description"
        }
        
        Returns:
        {
            "id": 1,
            "file_url": "videos/20250118/abc123.mp4",
            "title": "My Video",
            ...
        }
        """
        try:
            file_path = request.data.get('file_path')
            file_type = request.data.get('file_type')
            title = request.data.get('title', 'Untitled')
            description = request.data.get('description', '')
            
            if not all([file_path, file_type]):
                return Response(
                    {'error': 'Missing required fields: file_path, file_type'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get storage service
            storage_service = get_storage_service()
            
            # Verify file exists in storage
            if not storage_service.file_exists(file_path):
                return Response(
                    {'error': 'File not found in storage'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get file metadata
            metadata = storage_service.get_file_metadata(file_path)
            
            # Create database record based on file type
            if file_type == 'video':
                # Determine file type from metadata
                content_type = metadata.get('content_type', '') if metadata else ''
                
                video = VideoAsset.objects.create(
                    title=title,
                    description=description,
                    storage_uri=file_path,
                    file_size=metadata.get('size', 0) if metadata else 0,
                    owner=request.user,
                    school=request.user.school,
                    grade='K',  # Default, should be updated by user
                    topic='fractions_basics',  # Default, should be updated by user
                    status='DRAFT'  # Start as draft
                )
                
                serializer = VideoAssetSerializer(video)
                logger.info(f"Video asset created: {video.id} by user {request.user.id}")
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
                
            elif file_type in ['resource', 'lesson']:
                # Determine file type from metadata
                content_type = metadata.get('content_type', '') if metadata else ''
                
                # Map MIME type to file_type
                file_type_map = {
                    'application/pdf': 'pdf',
                    'application/msword': 'doc',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
                    'application/vnd.ms-powerpoint': 'ppt',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'pptx',
                    'application/vnd.ms-excel': 'xls',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'xlsx',
                    'text/plain': 'txt',
                    'image/jpeg': 'image',
                    'image/png': 'image',
                    'image/gif': 'image',
                }
                resource_file_type = file_type_map.get(content_type, 'other')
                
                resource = Resource.objects.create(
                    title=title,
                    description=description,
                    file_uri=file_path,
                    file_size=metadata.get('size', 0) if metadata else 0,
                    file_type=resource_file_type,
                    owner=request.user,
                    school=request.user.school,
                    status='DRAFT'  # Start as draft
                )
                
                serializer = ResourceSerializer(resource)
                logger.info(f"Resource created: {resource.id} by user {request.user.id}")
                
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            
            else:
                return Response(
                    {'error': f'Unsupported file type: {file_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"Error confirming upload: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to confirm upload'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'], url_path='get-download-url')
    def get_download_url(self, request):
        """
        Generate a signed download URL for a file
        
        POST /api/content/uploads/get-download-url/
        Body:
        {
            "file_path": "videos/20250118/abc123.mp4",
            "expiration_minutes": 60
        }
        
        Returns:
        {
            "download_url": "https://storage.googleapis.com/...",
            "expires_in": 3600
        }
        """
        try:
            file_path = request.data.get('file_path')
            expiration_minutes = request.data.get('expiration_minutes', 60)
            
            if not file_path:
                return Response(
                    {'error': 'Missing required field: file_path'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get storage service
            storage_service = get_storage_service()
            
            # Verify file exists
            if not storage_service.file_exists(file_path):
                return Response(
                    {'error': 'File not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Generate download URL
            download_url = storage_service.generate_download_url(
                file_path=file_path,
                expiration_minutes=expiration_minutes
            )
            
            logger.info(
                f"Download URL generated for user {request.user.id}: {file_path}"
            )
            
            return Response({
                'download_url': download_url,
                'expires_in': expiration_minutes * 60
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating download URL: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to generate download URL'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['delete'], url_path='delete-file')
    def delete_file(self, request):
        """
        Delete a file from storage
        
        DELETE /api/content/uploads/delete-file/
        Body:
        {
            "file_path": "videos/20250118/abc123.mp4"
        }
        
        Returns:
        {
            "message": "File deleted successfully"
        }
        """
        try:
            file_path = request.data.get('file_path')
            
            if not file_path:
                return Response(
                    {'error': 'Missing required field: file_path'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get storage service
            storage_service = get_storage_service()
            
            # Delete file
            success = storage_service.delete_file(file_path)
            
            if success:
                logger.info(
                    f"File deleted by user {request.user.id}: {file_path}"
                )
                return Response({
                    'message': 'File deleted successfully'
                }, status=status.HTTP_200_OK)
            else:
                return Response(
                    {'error': 'Failed to delete file'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.error(f"Error deleting file: {e}", exc_info=True)
            return Response(
                {'error': 'Failed to delete file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['GET'])
@permission_classes([require_permission('activities_view')])
def get_streaming_url(request, video_id):
    """
    Get a streaming URL for a video
    
    GET /api/content/videos/{video_id}/stream/
    
    Returns:
    {
        "streaming_url": "https://storage.googleapis.com/...",
        "expires_in": 3600
    }
    """
    try:
        video = VideoAsset.objects.get(id=video_id)
        
        # Enforce school and visibility constraints at object level.
        if video.school != request.user.school:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        if not request.user.can('video_stream', obj=video):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Use model method to generate streaming URL
        streaming_url = video.get_streaming_url(expiration_minutes=60)
        
        logger.info(
            f"Streaming URL generated for user {request.user.id}: video {video_id}"
        )
        
        return Response({
            'streaming_url': streaming_url,
            'expires_in': 3600,
            'video_id': str(video.id),
            'title': video.title
        }, status=status.HTTP_200_OK)
        
    except VideoAsset.DoesNotExist:
        return Response(
            {'error': 'Video not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error generating streaming URL: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to generate streaming URL'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([require_permission('resources_download')])
def get_resource_download_url(request, resource_id):
    """
    Get a download URL for a resource
    
    GET /api/content/resources/{resource_id}/download/
    
    Returns:
    {
        "download_url": "https://storage.googleapis.com/...",
        "expires_in": 3600,
        "file_name": "document.pdf"
    }
    """
    try:
        resource = Resource.objects.get(id=resource_id)
        
        # Enforce school and visibility constraints at object level.
        if resource.school != request.user.school:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        if not request.user.can('resource_download', obj=resource):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        # Use model method to generate download URL
        download_url = resource.get_download_url(expiration_minutes=60)
        
        logger.info(
            f"Download URL generated for user {request.user.id}: resource {resource_id}"
        )
        
        return Response({
            'download_url': download_url,
            'expires_in': 3600,
            'resource_id': str(resource.id),
            'file_name': resource.title,
            'file_type': resource.file_type
        }, status=status.HTTP_200_OK)
        
    except Resource.DoesNotExist:
        return Response(
            {'error': 'Resource not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Error generating download URL: {e}", exc_info=True)
        return Response(
            {'error': 'Failed to generate download URL'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

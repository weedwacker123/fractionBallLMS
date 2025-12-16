"""
Simple file upload views with Firebase Storage integration
All files are stored in Firebase Cloud Storage
"""
import logging
import mimetypes
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
from .models import VideoAsset, Resource
from .services import FirebaseStorageService

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["GET", "POST"])
def simple_upload_view(request):
    """
    Simple file upload view for videos and resources
    All files are uploaded to Firebase Cloud Storage
    """
    if request.method == 'POST':
        try:
            # Get uploaded file
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                messages.error(request, 'Please select a file to upload')
                return render(request, 'simple_upload.html')
            
            # Get metadata
            title = request.POST.get('title', uploaded_file.name)
            description = request.POST.get('description', '')
            grade = request.POST.get('grade', '')
            topic = request.POST.get('topic', '')
            file_type = request.POST.get('file_type', 'video')
            
            # Validate file size
            max_size = 500 * 1024 * 1024  # 500MB for videos
            if file_type == 'resource':
                max_size = 50 * 1024 * 1024  # 50MB for resources
            
            if uploaded_file.size > max_size:
                max_mb = max_size / (1024 * 1024)
                messages.error(request, f'File too large. Maximum size is {max_mb:.0f}MB')
                return render(request, 'simple_upload.html')
            
            # Initialize Firebase Storage service
            firebase_service = FirebaseStorageService()
            
            # Check if Firebase is configured
            if not firebase_service.bucket:
                logger.error("Firebase Storage not configured")
                messages.error(request, '❌ Firebase Storage is not configured. Please contact your administrator.')
                return render(request, 'simple_upload.html')
            
            # Get content type
            content_type = uploaded_file.content_type or mimetypes.guess_type(uploaded_file.name)[0] or 'application/octet-stream'
            
            # Upload to Firebase
            logger.info(f"Uploading {uploaded_file.name} to Firebase Storage...")
            result = firebase_service.upload_file_direct(
                file_obj=uploaded_file,
                filename=uploaded_file.name,
                content_type=content_type,
                file_category=file_type,
                user_id=request.user.id,
                school_id=request.user.school.id if request.user.school else None
            )
            
            file_path = result['storage_path']
            firebase_url = result['public_url']
            logger.info(f"✅ Uploaded to Firebase: {file_path}")
            
            # Create database record
            if file_type == 'video':
                video = VideoAsset.objects.create(
                    title=title,
                    description=description,
                    storage_uri=firebase_url,
                    file_size=uploaded_file.size,
                    grade=grade or 'K',
                    topic=topic or 'fractions_basics',
                    owner=request.user,
                    school=request.user.school,
                    status='DRAFT'
                )
                messages.success(request, f'🔥 Video "{title}" uploaded to Firebase Cloud Storage!')
                logger.info(f"Video uploaded: {video.id} by {request.user.username} to Firebase")
            else:
                # Map file extension to resource type
                ext = uploaded_file.name.split('.')[-1].lower()
                resource_type_map = {
                    'pdf': 'pdf',
                    'doc': 'doc',
                    'docx': 'docx',
                    'ppt': 'ppt',
                    'pptx': 'pptx',
                    'xls': 'xls',
                    'xlsx': 'xlsx',
                    'txt': 'txt',
                    'jpg': 'image',
                    'jpeg': 'image',
                    'png': 'image',
                    'gif': 'image'
                }
                resource_file_type = resource_type_map.get(ext, 'other')
                
                resource = Resource.objects.create(
                    title=title,
                    description=description,
                    file_uri=firebase_url,
                    file_size=uploaded_file.size,
                    file_type=resource_file_type,
                    grade=grade,
                    topic=topic,
                    owner=request.user,
                    school=request.user.school,
                    status='DRAFT'
                )
                messages.success(request, f'🔥 Resource "{title}" uploaded to Firebase Cloud Storage!')
                logger.info(f"Resource uploaded: {resource.id} by {request.user.username} to Firebase")
            
            return redirect('simple-upload')
            
        except Exception as e:
            logger.error(f"Upload error: {e}", exc_info=True)
            messages.error(request, f'❌ Upload failed: {str(e)}')
            return render(request, 'simple_upload.html')
    
    # GET request - show upload form
    return render(request, 'simple_upload.html')


@login_required
def my_uploads_view(request):
    """
    View user's uploaded videos and resources
    """
    videos = VideoAsset.objects.filter(owner=request.user).order_by('-created_at')[:20]
    resources = Resource.objects.filter(owner=request.user).order_by('-created_at')[:20]
    
    context = {
        'videos': videos,
        'resources': resources
    }
    return render(request, 'my_uploads.html', context)


@login_required
@require_POST
def delete_video(request, video_id):
    """
    Delete a video that belongs to the current user
    """
    try:
        logger.info(f"Delete video request: video_id={video_id}, user={request.user.username}, is_authenticated={request.user.is_authenticated}, user_id={request.user.id}")
        
        # Try to get the video
        try:
            video = VideoAsset.objects.get(id=video_id)
        except VideoAsset.DoesNotExist:
            logger.error(f"Video not found: {video_id}")
            return JsonResponse({
                'success': False,
                'message': 'Video not found'
            }, status=404)
        
        # Check ownership
        if video.owner != request.user:
            logger.warning(f"Unauthorized delete attempt: video={video_id}, user={request.user.username} (id={request.user.id}), owner={video.owner.username} (id={video.owner.id})")
            return JsonResponse({
                'success': False,
                'message': f'You do not have permission to delete this video. Video belongs to {video.owner.username}, you are {request.user.username}'
            }, status=403)
        
        # Delete from Firebase Storage (optional - commented out for safety)
        # try:
        #     firebase_service = FirebaseStorageService()
        #     if firebase_service.bucket and video.storage_uri:
        #         # Extract storage path from URL and delete
        #         pass
        # except Exception as e:
        #     logger.warning(f"Failed to delete file from Firebase: {e}")
        
        # Delete from database
        video_title = video.title
        video.delete()
        
        logger.info(f"Video deleted successfully: {video_id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f'Video "{video_title}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to delete video {video_id}: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Failed to delete video: {str(e)}'
        }, status=500)


@login_required
@require_POST
def delete_resource(request, resource_id):
    """
    Delete a resource that belongs to the current user
    """
    try:
        logger.info(f"Delete resource request: resource_id={resource_id}, user={request.user.username}")
        
        # Try to get the resource
        try:
            resource = Resource.objects.get(id=resource_id)
        except Resource.DoesNotExist:
            logger.error(f"Resource not found: {resource_id}")
            return JsonResponse({
                'success': False,
                'message': 'Resource not found'
            }, status=404)
        
        # Check ownership
        if resource.owner != request.user:
            logger.warning(f"Unauthorized delete attempt: resource={resource_id}, user={request.user.username}, owner={resource.owner.username}")
            return JsonResponse({
                'success': False,
                'message': 'You do not have permission to delete this resource'
            }, status=403)
        
        # Delete from Firebase Storage (optional - commented out for safety)
        # try:
        #     firebase_service = FirebaseStorageService()
        #     if firebase_service.bucket and resource.file_uri:
        #         # Extract storage path from URL and delete
        #         pass
        # except Exception as e:
        #     logger.warning(f"Failed to delete file from Firebase: {e}")
        
        # Delete from database
        resource_title = resource.title
        resource.delete()
        
        logger.info(f"Resource deleted successfully: {resource_id} by {request.user.username}")
        
        return JsonResponse({
            'success': True,
            'message': f'Resource "{resource_title}" deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to delete resource {resource_id}: {e}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'Failed to delete resource: {str(e)}'
        }, status=500)



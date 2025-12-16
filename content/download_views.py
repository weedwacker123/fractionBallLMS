"""
Resource download views with tracking
"""
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Resource, AssetDownload
import logging

logger = logging.getLogger(__name__)


@login_required
def track_and_download_resource(request, resource_id):
    """
    Track resource download and redirect to signed URL
    """
    try:
        resource = get_object_or_404(Resource, id=resource_id)
        
        # Check if resource is accessible (published or owned by user)
        if resource.status != 'PUBLISHED' and resource.owner != request.user:
            return JsonResponse({
                'success': False,
                'message': 'Resource not accessible'
            }, status=403)
        
        # Track download
        try:
            AssetDownload.objects.create(
                resource=resource,
                user=request.user,
                file_size=resource.file_size,
                download_completed=True,
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]  # Truncate to fit field
            )
            logger.info(f"Download tracked: {resource.title} by {request.user.username}")
        except Exception as e:
            logger.error(f"Failed to track download: {e}")
        
        # Generate signed download URL
        download_url = resource.get_download_url(expiration_minutes=10)
        
        # Redirect to signed URL
        return redirect(download_url)
        
    except Exception as e:
        logger.error(f"Download error: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Download failed: {str(e)}'
        }, status=500)


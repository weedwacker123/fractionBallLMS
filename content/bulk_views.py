"""
Bulk upload views for CSV content ingestion
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from django.http import HttpResponse
from accounts.permissions import require_permission
from .bulk_upload import create_bulk_upload_job, get_job_status
from .models import AuditLog
import csv
import io
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(['POST'])
@permission_classes([require_permission('bulk.upload')])
@parser_classes([MultiPartParser, FormParser])
def upload_csv(request):
    """
    Upload CSV file for bulk content import
    POST /api/bulk/upload/
    """
    try:
        # Validate file upload
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        uploaded_file = request.FILES['file']
        file_type = request.data.get('type', 'video')  # 'video' or 'resource'
        
        # Validate file type
        if file_type not in ['video', 'resource']:
            return Response(
                {'error': 'Invalid type. Must be "video" or "resource"'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file format
        if not uploaded_file.name.lower().endswith('.csv'):
            return Response(
                {'error': 'File must be a CSV file'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if uploaded_file.size > max_size:
            return Response(
                {'error': f'File too large. Maximum size is {max_size // (1024*1024)}MB'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Read file content
        try:
            file_content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return Response(
                {'error': 'File must be UTF-8 encoded'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Basic CSV validation
        try:
            csv_reader = csv.DictReader(io.StringIO(file_content))
            headers = csv_reader.fieldnames
            row_count = sum(1 for _ in csv_reader)
            
            if row_count == 0:
                return Response(
                    {'error': 'CSV file is empty'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if row_count > 1000:
                return Response(
                    {'error': 'CSV file too large. Maximum 1000 rows allowed'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            return Response(
                {'error': f'Invalid CSV format: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate required headers
        required_headers = {
            'video': ['title', 'storage_uri'],
            'resource': ['title', 'file_uri', 'file_type']
        }
        
        missing_headers = []
        for required_header in required_headers[file_type]:
            if required_header not in headers:
                missing_headers.append(required_header)
        
        if missing_headers:
            return Response({
                'error': f'Missing required CSV headers: {", ".join(missing_headers)}',
                'required_headers': required_headers[file_type],
                'found_headers': list(headers) if headers else []
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create and queue bulk upload job
        job_id, initial_results = create_bulk_upload_job(
            user=request.user,
            file_content=file_content,
            file_type=file_type
        )
        
        # Log upload initiation
        AuditLog.objects.create(
            action='BULK_UPLOAD_STARTED',
            user=request.user,
            metadata={
                'job_id': job_id,
                'file_name': uploaded_file.name,
                'file_size': uploaded_file.size,
                'content_type': file_type,
                'row_count': row_count,
                'headers': list(headers) if headers else []
            },
            ip_address=get_client_ip(request)
        )
        
        return Response({
            'message': 'File uploaded successfully and processing started',
            'job_id': job_id,
            'file_info': {
                'name': uploaded_file.name,
                'size': uploaded_file.size,
                'type': file_type,
                'rows': row_count,
                'headers': list(headers) if headers else []
            },
            'initial_status': initial_results
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Bulk upload failed for user {request.user.id}: {e}")
        return Response(
            {'error': 'Upload failed', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([require_permission('bulk.upload')])
def job_status(request, job_id):
    """
    Get status of a bulk upload job
    GET /api/bulk/jobs/{job_id}/status/
    """
    try:
        job_data = get_job_status(job_id)
        
        if not job_data:
            return Response(
                {'error': 'Job not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify job belongs to current user (or user is admin)
        if (str(request.user.id) != job_data.get('user_id') and
            not request.user.can('users.manage')):
            return Response(
                {'error': 'Access denied'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return Response({
            'job_id': job_id,
            'status': job_data
        })
        
    except Exception as e:
        logger.error(f"Failed to get job status {job_id}: {e}")
        return Response(
            {'error': 'Failed to get job status', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([require_permission('bulk.upload')])
def my_upload_jobs(request):
    """
    Get list of user's bulk upload jobs
    GET /api/bulk/jobs/
    """
    try:
        # In a real implementation, you'd query a database or job queue
        # For now, we'll return a simplified response
        
        # Get recent audit logs for this user's bulk uploads
        recent_uploads = AuditLog.objects.filter(
            user=request.user,
            action='BULK_UPLOAD_STARTED'
        ).order_by('-created_at')[:10]
        
        jobs_data = []
        for log in recent_uploads:
            job_id = log.metadata.get('job_id')
            if job_id:
                job_status_data = get_job_status(job_id)
                jobs_data.append({
                    'job_id': job_id,
                    'file_name': log.metadata.get('file_name'),
                    'content_type': log.metadata.get('content_type'),
                    'row_count': log.metadata.get('row_count'),
                    'started_at': log.created_at,
                    'current_status': job_status_data.get('status') if job_status_data else 'UNKNOWN'
                })
        
        return Response({
            'jobs': jobs_data,
            'total_jobs': len(jobs_data)
        })
        
    except Exception as e:
        logger.error(f"Failed to get user jobs for {request.user.id}: {e}")
        return Response(
            {'error': 'Failed to get jobs list', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([require_permission('bulk.upload')])
def school_upload_jobs(request):
    """
    Get bulk upload jobs for school (school admin) or all schools (system admin)
    GET /api/bulk/jobs/school/
    """
    try:
        # Filter logs based on user permissions
        if request.user.can('schools.manage'):
            # System admin sees all
            logs_query = AuditLog.objects.filter(action='BULK_UPLOAD_STARTED')
        elif request.user.can('users.manage'):
            # School admin sees only their school
            school_users = User.objects.filter(school=request.user.school)
            logs_query = AuditLog.objects.filter(
                action='BULK_UPLOAD_STARTED',
                user__in=school_users
            )
        else:
            return Response(
                {'error': 'Insufficient permissions'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        recent_uploads = logs_query.select_related('user').order_by('-created_at')[:50]
        
        jobs_data = []
        for log in recent_uploads:
            job_id = log.metadata.get('job_id')
            job_status_data = get_job_status(job_id) if job_id else None
            
            jobs_data.append({
                'job_id': job_id,
                'user_name': log.user.get_full_name(),
                'user_email': log.user.email,
                'school_name': log.user.school.name if log.user.school else 'Unknown',
                'file_name': log.metadata.get('file_name'),
                'content_type': log.metadata.get('content_type'),
                'row_count': log.metadata.get('row_count'),
                'started_at': log.created_at,
                'current_status': job_status_data.get('status') if job_status_data else 'UNKNOWN',
                'success_count': job_status_data.get('successful_imports', 0) if job_status_data else 0,
                'error_count': job_status_data.get('failed_imports', 0) if job_status_data else 0
            })
        
        return Response({
            'jobs': jobs_data,
            'total_jobs': len(jobs_data)
        })
        
    except Exception as e:
        logger.error(f"Failed to get school jobs: {e}")
        return Response(
            {'error': 'Failed to get jobs list', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([require_permission('bulk.upload')])
def download_template(request):
    """
    Download CSV template for bulk uploads
    GET /api/bulk/template/?type=video
    """
    try:
        file_type = request.query_params.get('type', 'video')
        
        if file_type not in ['video', 'resource']:
            return Response(
                {'error': 'Invalid type. Must be "video" or "resource"'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create CSV template
        output = io.StringIO()
        
        if file_type == 'video':
            headers = [
                'title', 'description', 'grade', 'topic', 'tags', 
                'duration', 'storage_uri', 'owner_email'
            ]
            sample_data = [
                [
                    'Sample Video Title',
                    'This is a sample description for the video content',
                    'K',
                    'fractions_basics',
                    'visual, beginner, interactive',
                    '300',
                    'https://firebasestorage.googleapis.com/v0/b/project/o/videos/sample.mp4',
                    'teacher@school.edu'
                ]
            ]
        else:  # resource
            headers = [
                'title', 'description', 'file_uri', 'file_type', 
                'grade', 'topic', 'tags', 'owner_email'
            ]
            sample_data = [
                [
                    'Sample Resource Title',
                    'This is a sample description for the resource',
                    'https://firebasestorage.googleapis.com/v0/b/project/o/resources/sample.pdf',
                    'pdf',
                    '1',
                    'fractions_basics',
                    'worksheet, practice',
                    'teacher@school.edu'
                ]
            ]
        
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(sample_data)
        
        # Create HTTP response
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="bulk_upload_template_{file_type}.csv"'
        
        return response
        
    except Exception as e:
        logger.error(f"Failed to generate template: {e}")
        return Response(
            {'error': 'Failed to generate template', 'message': str(e)},
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









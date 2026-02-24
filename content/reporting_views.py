"""
Reporting views for CSV exports and analytics reporting
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from django.http import HttpResponse, StreamingHttpResponse
from datetime import datetime, timedelta
from accounts.permissions import require_permission
from .models import VideoAsset, Resource, AssetView, AssetDownload, AuditLog
from accounts.models import School
import csv
import io
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Echo:
    """An object that implements just the write method of the file-like interface."""
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value


@api_view(['GET'])
@permission_classes([require_permission('cms_view')])
def export_views_report(request):
    """
    Export video views report as CSV
    GET /api/reports/views/?start_date=2024-01-01&end_date=2024-01-31&school_id=uuid
    """
    try:
        # Parse date parameters
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        school_id = request.query_params.get('school_id')
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date parameters are required (YYYY-MM-DD format)'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if start_date > end_date:
            return Response(
                {'error': 'start_date cannot be after end_date'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build queryset based on permissions
        views_query = AssetView.objects.select_related(
            'asset', 'asset__owner', 'asset__school', 'user'
        ).filter(
            viewed_at__date__gte=start_date,
            viewed_at__date__lte=end_date
        )
        
        if not request.user.is_admin and request.user.school:
            # School admin can only see their school's data
            views_query = views_query.filter(asset__school=request.user.school)
        elif school_id and request.user.is_admin:
            # System admin can filter by specific school
            try:
                views_query = views_query.filter(asset__school_id=school_id)
            except ValueError:
                return Response(
                    {'error': 'Invalid school_id format'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create streaming CSV response
        def generate_csv_rows():
            # CSV headers
            yield [
                'Date', 'Video Title', 'Video Owner', 'School', 'Grade', 'Topic',
                'Viewer Name', 'Viewer Email', 'Duration Watched (seconds)', 
                'Completion Percentage', 'Session ID', 'Viewed At'
            ]
            
            # Data rows
            for view in views_query.iterator(chunk_size=1000):
                yield [
                    view.viewed_at.date().isoformat(),
                    view.asset.title,
                    view.asset.owner.get_full_name(),
                    view.asset.school.name,
                    view.asset.get_grade_display() if view.asset.grade else '',
                    view.asset.get_topic_display() if view.asset.topic else '',
                    view.user.get_full_name(),
                    view.user.email,
                    view.duration_watched or '',
                    view.completion_percentage or '',
                    view.session_id,
                    view.viewed_at.isoformat()
                ]
        
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in generate_csv_rows()),
            content_type="text/csv"
        )
        
        filename = f"video_views_report_{start_date}_{end_date}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Log export
        AuditLog.objects.create(
            action='REPORT_EXPORTED',
            user=request.user,
            metadata={
                'report_type': 'video_views',
                'start_date': start_date_str,
                'end_date': end_date_str,
                'school_id': school_id,
                'filename': filename
            },
            ip_address=get_client_ip(request)
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Views report export failed: {e}")
        return Response(
            {'error': 'Failed to export views report', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([require_permission('cms_view')])
def export_downloads_report(request):
    """
    Export resource downloads report as CSV
    GET /api/reports/downloads/?start_date=2024-01-01&end_date=2024-01-31&school_id=uuid
    """
    try:
        # Parse parameters (same logic as views report)
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        school_id = request.query_params.get('school_id')
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date parameters are required (YYYY-MM-DD format)'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build queryset
        downloads_query = AssetDownload.objects.select_related(
            'resource', 'resource__owner', 'resource__school', 'user'
        ).filter(
            downloaded_at__date__gte=start_date,
            downloaded_at__date__lte=end_date
        )
        
        if not request.user.is_admin and request.user.school:
            downloads_query = downloads_query.filter(resource__school=request.user.school)
        elif school_id and request.user.is_admin:
            try:
                downloads_query = downloads_query.filter(resource__school_id=school_id)
            except ValueError:
                return Response(
                    {'error': 'Invalid school_id format'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create streaming CSV response
        def generate_csv_rows():
            yield [
                'Date', 'Resource Title', 'Resource Owner', 'School', 'File Type',
                'Grade', 'Topic', 'Downloader Name', 'Downloader Email',
                'File Size (bytes)', 'Download Completed', 'Downloaded At'
            ]
            
            for download in downloads_query.iterator(chunk_size=1000):
                yield [
                    download.downloaded_at.date().isoformat(),
                    download.resource.title,
                    download.resource.owner.get_full_name(),
                    download.resource.school.name,
                    download.resource.get_file_type_display(),
                    download.resource.get_grade_display() if download.resource.grade else '',
                    download.resource.get_topic_display() if download.resource.topic else '',
                    download.user.get_full_name(),
                    download.user.email,
                    download.file_size or '',
                    'Yes' if download.download_completed else 'No',
                    download.downloaded_at.isoformat()
                ]
        
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in generate_csv_rows()),
            content_type="text/csv"
        )
        
        filename = f"resource_downloads_report_{start_date}_{end_date}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Log export
        AuditLog.objects.create(
            action='REPORT_EXPORTED',
            user=request.user,
            metadata={
                'report_type': 'resource_downloads',
                'start_date': start_date_str,
                'end_date': end_date_str,
                'school_id': school_id,
                'filename': filename
            },
            ip_address=get_client_ip(request)
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Downloads report export failed: {e}")
        return Response(
            {'error': 'Failed to export downloads report', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([require_permission('cms_view')])
def export_content_report(request):
    """
    Export content inventory report as CSV
    GET /api/reports/content/?school_id=uuid&status=PUBLISHED
    """
    try:
        school_id = request.query_params.get('school_id')
        status_filter = request.query_params.get('status')
        content_type = request.query_params.get('type', 'video')  # 'video' or 'resource'
        
        if content_type not in ['video', 'resource']:
            return Response(
                {'error': 'Invalid type. Must be "video" or "resource"'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Build queryset
        if content_type == 'video':
            content_query = VideoAsset.objects.select_related(
                'owner', 'school', 'reviewed_by'
            ).all()
        else:
            content_query = Resource.objects.select_related(
                'owner', 'school'
            ).all()
        
        # Apply filters
        if not request.user.is_admin and request.user.school:
            content_query = content_query.filter(school=request.user.school)
        elif school_id and request.user.is_admin:
            try:
                content_query = content_query.filter(school_id=school_id)
            except ValueError:
                return Response(
                    {'error': 'Invalid school_id format'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        if status_filter:
            content_query = content_query.filter(status=status_filter)
        
        # Create streaming CSV response
        def generate_csv_rows():
            if content_type == 'video':
                yield [
                    'Title', 'Description', 'Owner', 'School', 'Grade', 'Topic',
                    'Duration (seconds)', 'File Size (bytes)', 'Status', 'Tags',
                    'Created At', 'Updated At', 'Submitted At', 'Reviewed By', 'Reviewed At'
                ]
                
                for video in content_query.iterator(chunk_size=1000):
                    yield [
                        video.title,
                        video.description,
                        video.owner.get_full_name(),
                        video.school.name,
                        video.get_grade_display() if video.grade else '',
                        video.get_topic_display() if video.topic else '',
                        video.duration or '',
                        video.file_size or '',
                        video.get_status_display(),
                        ', '.join(video.tags) if video.tags else '',
                        video.created_at.isoformat(),
                        video.updated_at.isoformat(),
                        video.submitted_at.isoformat() if video.submitted_at else '',
                        video.reviewed_by.get_full_name() if video.reviewed_by else '',
                        video.reviewed_at.isoformat() if video.reviewed_at else ''
                    ]
            else:  # resource
                yield [
                    'Title', 'Description', 'Owner', 'School', 'File Type',
                    'Grade', 'Topic', 'File Size (bytes)', 'Status', 'Tags',
                    'Created At', 'Updated At'
                ]
                
                for resource in content_query.iterator(chunk_size=1000):
                    yield [
                        resource.title,
                        resource.description,
                        resource.owner.get_full_name(),
                        resource.school.name,
                        resource.get_file_type_display(),
                        resource.get_grade_display() if resource.grade else '',
                        resource.get_topic_display() if resource.topic else '',
                        resource.file_size or '',
                        resource.get_status_display(),
                        ', '.join(resource.tags) if resource.tags else '',
                        resource.created_at.isoformat(),
                        resource.updated_at.isoformat()
                    ]
        
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in generate_csv_rows()),
            content_type="text/csv"
        )
        
        filename = f"{content_type}_inventory_report_{timezone.now().strftime('%Y%m%d')}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Log export
        AuditLog.objects.create(
            action='REPORT_EXPORTED',
            user=request.user,
            metadata={
                'report_type': f'{content_type}_inventory',
                'school_id': school_id,
                'status_filter': status_filter,
                'filename': filename
            },
            ip_address=get_client_ip(request)
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Content report export failed: {e}")
        return Response(
            {'error': 'Failed to export content report', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([require_permission('cms_view')])
def export_analytics_summary(request):
    """
    Export analytics summary report as CSV
    GET /api/reports/analytics-summary/?start_date=2024-01-01&end_date=2024-01-31
    """
    try:
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        if not start_date_str or not end_date_str:
            return Response(
                {'error': 'start_date and end_date parameters are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get school filter
        school_filter = Q()
        if not request.user.is_admin and request.user.school:
            school_filter = Q(school=request.user.school)
        
        # Get video analytics
        video_analytics = VideoAsset.objects.filter(school_filter).annotate(
            total_views=Count(
                'views', 
                filter=Q(views__viewed_at__date__gte=start_date, views__viewed_at__date__lte=end_date)
            ),
            unique_viewers=Count(
                'views__user',
                distinct=True,
                filter=Q(views__viewed_at__date__gte=start_date, views__viewed_at__date__lte=end_date)
            ),
            avg_completion=Avg(
                'views__completion_percentage',
                filter=Q(views__viewed_at__date__gte=start_date, views__viewed_at__date__lte=end_date)
            ),
            total_watch_time=Sum(
                'views__duration_watched',
                filter=Q(views__viewed_at__date__gte=start_date, views__viewed_at__date__lte=end_date)
            )
        ).filter(total_views__gt=0).order_by('-total_views')
        
        # Create CSV response
        def generate_csv_rows():
            yield [
                'Content Title', 'Content Type', 'Owner', 'School', 'Grade', 'Topic',
                'Total Views', 'Unique Viewers', 'Total Watch Time (seconds)', 
                'Average Completion Rate', 'Status', 'Created Date'
            ]
            
            for video in video_analytics.iterator(chunk_size=1000):
                yield [
                    video.title,
                    'Video',
                    video.owner.get_full_name(),
                    video.school.name,
                    video.get_grade_display() if video.grade else '',
                    video.get_topic_display() if video.topic else '',
                    video.total_views,
                    video.unique_viewers,
                    video.total_watch_time or 0,
                    f"{(video.avg_completion or 0) * 100:.1f}%",
                    video.get_status_display(),
                    video.created_at.date().isoformat()
                ]
        
        pseudo_buffer = Echo()
        writer = csv.writer(pseudo_buffer)
        response = StreamingHttpResponse(
            (writer.writerow(row) for row in generate_csv_rows()),
            content_type="text/csv"
        )
        
        filename = f"analytics_summary_{start_date}_{end_date}.csv"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Analytics summary export failed: {e}")
        return Response(
            {'error': 'Failed to export analytics summary', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([require_permission('cms_view')])
def reports_dashboard(request):
    """
    Reports dashboard with available reports and recent exports
    GET /api/reports/dashboard/
    """
    try:
        # Available reports
        available_reports = [
            {
                'name': 'Video Views Report',
                'description': 'Detailed video viewing data with completion rates',
                'endpoint': '/api/reports/views/',
                'parameters': ['start_date', 'end_date', 'school_id (admin only)'],
                'format': 'CSV'
            },
            {
                'name': 'Resource Downloads Report',
                'description': 'Resource download activity and completion tracking',
                'endpoint': '/api/reports/downloads/',
                'parameters': ['start_date', 'end_date', 'school_id (admin only)'],
                'format': 'CSV'
            },
            {
                'name': 'Content Inventory Report',
                'description': 'Complete inventory of videos and resources',
                'endpoint': '/api/reports/content/',
                'parameters': ['type (video/resource)', 'status', 'school_id (admin only)'],
                'format': 'CSV'
            },
            {
                'name': 'Analytics Summary Report',
                'description': 'Aggregated analytics with top performing content',
                'endpoint': '/api/reports/analytics-summary/',
                'parameters': ['start_date', 'end_date'],
                'format': 'CSV'
            }
        ]
        
        # Recent exports by current user
        recent_exports = AuditLog.objects.filter(
            user=request.user,
            action='REPORT_EXPORTED'
        ).order_by('-created_at')[:10]
        
        exports_data = []
        for export in recent_exports:
            exports_data.append({
                'report_type': export.metadata.get('report_type'),
                'filename': export.metadata.get('filename'),
                'parameters': {
                    'start_date': export.metadata.get('start_date'),
                    'end_date': export.metadata.get('end_date'),
                    'school_id': export.metadata.get('school_id'),
                },
                'exported_at': export.created_at
            })
        
        # Usage statistics
        total_exports = AuditLog.objects.filter(
            action='REPORT_EXPORTED'
        ).count()
        
        user_exports = AuditLog.objects.filter(
            user=request.user,
            action='REPORT_EXPORTED'
        ).count()
        
        return Response({
            'available_reports': available_reports,
            'recent_exports': exports_data,
            'usage_stats': {
                'total_system_exports': total_exports,
                'user_exports': user_exports
            },
            'user_permissions': {
                'can_export_school_data': request.user.can('cms_view') and bool(request.user.school),
                'can_export_all_schools': request.user.is_admin,
                'school_name': request.user.school.name if request.user.school else None
            }
        })
        
    except Exception as e:
        logger.error(f"Reports dashboard failed: {e}")
        return Response(
            {'error': 'Failed to load reports dashboard', 'message': str(e)},
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









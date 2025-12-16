"""
Analytics and Reporting views for teachers and administrators
Provides insights into content usage, engagement, and performance
"""
import csv
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from .models import (
    VideoAsset, Resource, Activity, AssetView, AssetDownload, 
    DailyAssetStats, ForumPost, ForumComment
)
import logging

logger = logging.getLogger(__name__)


@login_required
def analytics_dashboard(request):
    """
    Main analytics dashboard showing key metrics and insights
    """
    # Get date range from request (default: last 30 days)
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Get user's school for filtering
    user_school = request.user.school
    
    # Overview Statistics
    total_videos = VideoAsset.objects.filter(
        school=user_school,
        status='PUBLISHED'
    ).count()
    
    total_resources = Resource.objects.filter(
        school=user_school,
        status='PUBLISHED'
    ).count()
    
    total_activities = Activity.objects.filter(is_published=True).count()
    
    # Engagement Metrics (last N days)
    total_views = AssetView.objects.filter(
        viewed_at__gte=start_date,
        asset__school=user_school
    ).count()
    
    total_downloads = AssetDownload.objects.filter(
        downloaded_at__gte=start_date,
        resource__school=user_school
    ).count()
    
    unique_viewers = AssetView.objects.filter(
        viewed_at__gte=start_date,
        asset__school=user_school
    ).values('user').distinct().count()
    
    # Popular Videos (Top 10 by views)
    popular_videos = VideoAsset.objects.filter(
        school=user_school,
        status='PUBLISHED'
    ).annotate(
        view_count=Count('views', filter=Q(views__viewed_at__gte=start_date))
    ).order_by('-view_count')[:10]
    
    # Popular Resources (Top 10 by downloads)
    popular_resources = Resource.objects.filter(
        school=user_school,
        status='PUBLISHED'
    ).annotate(
        download_count=Count('downloads', filter=Q(downloads__downloaded_at__gte=start_date))
    ).order_by('-download_count')[:10]
    
    # Recent Activity (last 20 views/downloads)
    recent_views = AssetView.objects.filter(
        asset__school=user_school,
        viewed_at__gte=start_date
    ).select_related('asset', 'user').order_by('-viewed_at')[:20]
    
    recent_downloads = AssetDownload.objects.filter(
        resource__school=user_school,
        downloaded_at__gte=start_date
    ).select_related('resource', 'user').order_by('-downloaded_at')[:20]
    
    # Community Engagement
    total_forum_posts = ForumPost.objects.count()
    total_forum_comments = ForumComment.objects.filter(is_deleted=False).count()
    recent_posts = ForumPost.objects.select_related('author', 'category').order_by('-created_at')[:5]
    
    # Grade-level breakdown
    videos_by_grade = VideoAsset.objects.filter(
        school=user_school,
        status='PUBLISHED'
    ).values('grade').annotate(count=Count('id')).order_by('grade')
    
    # View trends (last 7 days)
    view_trends = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        views = AssetView.objects.filter(
            asset__school=user_school,
            viewed_at__date=date
        ).count()
        view_trends.append({
            'date': date.strftime('%m/%d'),
            'views': views
        })
    view_trends.reverse()
    
    context = {
        'days': days,
        'start_date': start_date,
        'total_videos': total_videos,
        'total_resources': total_resources,
        'total_activities': total_activities,
        'total_views': total_views,
        'total_downloads': total_downloads,
        'unique_viewers': unique_viewers,
        'popular_videos': popular_videos,
        'popular_resources': popular_resources,
        'recent_views': recent_views,
        'recent_downloads': recent_downloads,
        'total_forum_posts': total_forum_posts,
        'total_forum_comments': total_forum_comments,
        'recent_posts': recent_posts,
        'videos_by_grade': videos_by_grade,
        'view_trends': view_trends,
    }
    
    return render(request, 'analytics_dashboard.html', context)


@login_required
def video_analytics(request, video_id):
    """
    Detailed analytics for a specific video
    """
    video = VideoAsset.objects.get(id=video_id, school=request.user.school)
    
    # Get date range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    
    # Total views
    total_views = video.views.filter(viewed_at__gte=start_date).count()
    unique_viewers = video.views.filter(viewed_at__gte=start_date).values('user').distinct().count()
    
    # Average completion rate
    avg_completion = video.views.filter(
        viewed_at__gte=start_date,
        completion_percentage__isnull=False
    ).aggregate(avg=Avg('completion_percentage'))['avg'] or 0
    
    # Views over time
    daily_views = video.views.filter(
        viewed_at__gte=start_date
    ).extra(
        select={'day': 'date(viewed_at)'}
    ).values('day').annotate(count=Count('id')).order_by('day')
    
    # Top viewers
    top_viewers = video.views.filter(
        viewed_at__gte=start_date
    ).values('user__username', 'user__email').annotate(
        view_count=Count('id')
    ).order_by('-view_count')[:10]
    
    context = {
        'video': video,
        'days': days,
        'total_views': total_views,
        'unique_viewers': unique_viewers,
        'avg_completion': avg_completion * 100,  # Convert to percentage
        'daily_views': list(daily_views),
        'top_viewers': top_viewers,
    }
    
    return render(request, 'video_analytics.html', context)


@login_required
def export_analytics_csv(request):
    """
    Export analytics data to CSV
    """
    # Get date range
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    export_type = request.GET.get('type', 'views')  # 'views' or 'downloads'
    
    user_school = request.user.school
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="analytics_{export_type}_{datetime.now().strftime("%Y%m%d")}.csv"'
    
    writer = csv.writer(response)
    
    if export_type == 'views':
        # Export video views
        writer.writerow(['Date', 'Video Title', 'User', 'Duration Watched (s)', 'Completion %', 'Referrer'])
        
        views = AssetView.objects.filter(
            asset__school=user_school,
            viewed_at__gte=start_date
        ).select_related('asset', 'user').order_by('-viewed_at')
        
        for view in views:
            writer.writerow([
                view.viewed_at.strftime('%Y-%m-%d %H:%M:%S'),
                view.asset.title,
                view.user.get_full_name() or view.user.username,
                view.duration_watched or 'N/A',
                f"{(view.completion_percentage * 100):.1f}" if view.completion_percentage else 'N/A',
                view.referrer or 'Direct'
            ])
    
    elif export_type == 'downloads':
        # Export resource downloads
        writer.writerow(['Date', 'Resource Title', 'User', 'File Type', 'File Size', 'Completed'])
        
        downloads = AssetDownload.objects.filter(
            resource__school=user_school,
            downloaded_at__gte=start_date
        ).select_related('resource', 'user').order_by('-downloaded_at')
        
        for download in downloads:
            writer.writerow([
                download.downloaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                download.resource.title,
                download.user.get_full_name() or download.user.username,
                download.resource.get_file_type_display(),
                download.resource.file_size_formatted,
                'Yes' if download.download_completed else 'No'
            ])
    
    elif export_type == 'summary':
        # Export summary statistics
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Report Period', f'Last {days} days'])
        writer.writerow(['Start Date', start_date.strftime('%Y-%m-%d')])
        writer.writerow(['End Date', timezone.now().strftime('%Y-%m-%d')])
        writer.writerow([])
        
        # Video statistics
        writer.writerow(['Videos'])
        writer.writerow(['Total Published Videos', VideoAsset.objects.filter(school=user_school, status='PUBLISHED').count()])
        writer.writerow(['Total Views', AssetView.objects.filter(asset__school=user_school, viewed_at__gte=start_date).count()])
        writer.writerow(['Unique Viewers', AssetView.objects.filter(asset__school=user_school, viewed_at__gte=start_date).values('user').distinct().count()])
        writer.writerow([])
        
        # Resource statistics
        writer.writerow(['Resources'])
        writer.writerow(['Total Published Resources', Resource.objects.filter(school=user_school, status='PUBLISHED').count()])
        writer.writerow(['Total Downloads', AssetDownload.objects.filter(resource__school=user_school, downloaded_at__gte=start_date).count()])
        writer.writerow([])
        
        # Top videos
        writer.writerow(['Top 10 Videos by Views'])
        writer.writerow(['Rank', 'Video Title', 'Views'])
        popular_videos = VideoAsset.objects.filter(
            school=user_school,
            status='PUBLISHED'
        ).annotate(
            view_count=Count('views', filter=Q(views__viewed_at__gte=start_date))
        ).order_by('-view_count')[:10]
        
        for i, video in enumerate(popular_videos, 1):
            writer.writerow([i, video.title, video.view_count])
    
    logger.info(f"Analytics CSV exported: type={export_type}, user={request.user.username}")
    return response


@login_required
def activity_engagement_json(request):
    """
    JSON endpoint for activity engagement data (for charts)
    """
    days = int(request.GET.get('days', 30))
    start_date = timezone.now() - timedelta(days=days)
    user_school = request.user.school
    
    # Get daily view counts for charts
    daily_data = []
    for i in range(days):
        date = (timezone.now() - timedelta(days=days-i-1)).date()
        views = AssetView.objects.filter(
            asset__school=user_school,
            viewed_at__date=date
        ).count()
        downloads = AssetDownload.objects.filter(
            resource__school=user_school,
            downloaded_at__date=date
        ).count()
        daily_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'views': views,
            'downloads': downloads
        })
    
    # Grade distribution
    grade_data = []
    for choice in ['K', '1', '2', '3', '4', '5', '6', '7', '8']:
        count = VideoAsset.objects.filter(
            school=user_school,
            status='PUBLISHED',
            grade=choice
        ).count()
        if count > 0:
            grade_data.append({
                'grade': choice,
                'count': count
            })
    
    return JsonResponse({
        'daily_engagement': daily_data,
        'grade_distribution': grade_data
    })


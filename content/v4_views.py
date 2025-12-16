"""
Views for Fraction Ball V4 interface
Educational activity-focused UI
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q
from .models import VideoAsset, Resource, Activity, AssetView, AssetDownload
import logging

logger = logging.getLogger(__name__)


def home(request):
    """
    Main home page with activity cards - dynamically loaded from database
    """
    # Get filter parameters
    selected_grade = request.GET.get('grade', '5')
    selected_topics = request.GET.getlist('topic', [])
    selected_location = request.GET.get('location', '')
    search_query = request.GET.get('q', '')
    
    # Build query
    activities = Activity.objects.filter(is_published=True)
    
    # Apply filters
    if selected_grade:
        activities = activities.filter(grade=selected_grade)
    
    if selected_location:
        activities = activities.filter(location=selected_location)
    
    if search_query:
        activities = activities.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by topics in Python (SQLite doesn't support JSON field lookups)
    if selected_topics:
        filtered_activities = []
        for activity in activities:
            activity_topics = activity.topics if isinstance(activity.topics, list) else []
            # Check if ANY of the selected topics are in this activity's topics
            if any(topic in activity_topics for topic in selected_topics):
                filtered_activities.append(activity)
        activities = filtered_activities
    else:
        activities = list(activities)
    
    # Order by defined order (only if it's a QuerySet, not a list)
    if not isinstance(activities, list):
        activities = activities.order_by('order', 'activity_number')
    else:
        # Sort the list manually
        activities = sorted(activities, key=lambda a: (a.order, a.activity_number))
    
    # Get all unique topics for filter buttons
    all_activities = Activity.objects.filter(is_published=True)
    all_topics = set()
    for activity in all_activities:
        all_topics.update(activity.topics if isinstance(activity.topics, list) else [])
    all_topics = sorted(list(all_topics))
    
    context = {
        'activities': activities,
        'selected_grade': selected_grade,
        'selected_topics': selected_topics,
        'selected_location': selected_location,
        'search_query': search_query,
        'all_topics': all_topics,
        'grade_choices': ['K', '1', '2', '3', '4', '5', '6', '7', '8'],
    }
    return render(request, 'home.html', context)


def activity_detail(request, slug):
    """
    Activity detail page with prerequisites, objectives, materials, etc.
    Dynamically loaded from database
    """
    activity = get_object_or_404(Activity, slug=slug, is_published=True)
    
    # Track view if user is authenticated and video exists
    if request.user.is_authenticated and activity.video_asset:
        try:
            session_id = request.session.session_key or 'anonymous'
            # Check if this session already viewed this video (to avoid duplicates)
            if not AssetView.objects.filter(
                asset=activity.video_asset,
                session_id=session_id
            ).exists():
                AssetView.objects.create(
                    asset=activity.video_asset,
                    user=request.user,
                    session_id=session_id,
                    referrer=request.META.get('HTTP_REFERER', '')
                )
                logger.info(f"View tracked: {activity.video_asset.title} by {request.user.username}")
        except Exception as e:
            logger.error(f"Failed to track view: {e}")
    
    # Get video streaming URL if available
    video_url = None
    if activity.video_asset:
        try:
            video_url = activity.video_asset.get_streaming_url(expiration_minutes=120)
        except Exception as e:
            logger.error(f"Error generating video URL: {e}")
    
    # Get resource download URLs (using tracking endpoint)
    teacher_resources = []
    for resource in activity.teacher_resources.all():
        teacher_resources.append({
            'resource': resource,
            'download_url': f'/download/resource/{resource.id}/'
        })
    
    student_resources = []
    for resource in activity.student_resources.all():
        student_resources.append({
            'resource': resource,
            'download_url': f'/download/resource/{resource.id}/'
        })
    
    # Get related activities (same grade, different activities)
    related_activities = Activity.objects.filter(
        is_published=True,
        grade=activity.grade
    ).exclude(id=activity.id).order_by('order', 'activity_number')[:3]
    
    context = {
        'activity': activity,
        'video_url': video_url,
        'teacher_resources': teacher_resources,
        'student_resources': student_resources,
        'related_activities': related_activities,
    }
    return render(request, 'activity_detail.html', context)


def community(request):
    """
    Community page for teacher collaboration
    """
    return render(request, 'community.html')


def faq(request):
    """
    FAQ page
    """
    return render(request, 'faq.html')


@login_required
def my_notes(request):
    """
    User's notes on activities
    """
    # Future implementation
    return render(request, 'notes.html')


def search_activities(request):
    """
    AJAX endpoint for searching/filtering activities
    Returns JSON for dynamic updates
    """
    # Get search parameters
    query = request.GET.get('q', '')
    grade = request.GET.get('grade', '')
    topics = request.GET.getlist('topic', [])
    location = request.GET.get('location', '')
    
    # Build query
    activities = Activity.objects.filter(is_published=True)
    
    # Apply filters
    if grade:
        activities = activities.filter(grade=grade)
    
    if location:
        activities = activities.filter(location=location)
    
    if query:
        activities = activities.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )
    
    # Filter by topics in Python (SQLite doesn't support JSON field lookups)
    if topics:
        filtered_activities = []
        for activity in activities:
            activity_topics = activity.topics if isinstance(activity.topics, list) else []
            # Check if ANY of the selected topics are in this activity's topics
            if any(topic in activity_topics for topic in topics):
                filtered_activities.append(activity)
        activities = filtered_activities
    else:
        activities = list(activities)
    
    # Order and prepare results
    if not isinstance(activities, list):
        activities = activities.order_by('order', 'activity_number')
    else:
        activities = sorted(activities, key=lambda a: (a.order, a.activity_number))
    
    # Return JSON if AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        results = []
        for activity in activities:
            results.append({
                'id': str(activity.id),
                'title': activity.title,
                'slug': activity.slug,
                'description': activity.description,
                'activity_number': activity.activity_number,
                'grade': activity.grade,
                'topics': activity.topics,
                'icon_type': activity.icon_type,
                'url': f'/activities/{activity.slug}/'
            })
        return JsonResponse({'activities': results})
    
    # Otherwise, render template with results
    context = {
        'activities': activities,
        'search_query': query,
        'selected_grade': grade,
        'selected_topics': topics,
        'selected_location': location,
    }
    return render(request, 'home.html', context)



























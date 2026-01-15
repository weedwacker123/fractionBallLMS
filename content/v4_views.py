"""
Views for Fraction Ball V4 interface
Educational activity-focused UI
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse, Http404
from django.db.models import Q
from django.conf import settings
from .models import VideoAsset, Resource, Activity, AssetView, AssetDownload
from . import firestore_service
from . import taxonomy_service
from .firestore_adapters import FirestoreActivity, FirestoreVideo, FirestoreResource
import logging

logger = logging.getLogger(__name__)

# Firebase Storage bucket name
FIREBASE_STORAGE_BUCKET = 'fractionball-lms.firebasestorage.app'


def get_storage_url(path: str) -> str:
    """
    Convert a Firebase Storage path to a full download URL.
    If the path is already a full URL, return it as-is.
    """
    if not path:
        return ''
    # If already a full URL, return as-is
    if path.startswith('http://') or path.startswith('https://'):
        return path
    # Convert storage path to full Firebase Storage URL
    # URL-encode the path (replace / with %2F)
    from urllib.parse import quote
    encoded_path = quote(path, safe='')
    return f"https://firebasestorage.googleapis.com/v0/b/{FIREBASE_STORAGE_BUCKET}/o/{encoded_path}?alt=media"


def home(request):
    """
    Main home page with activity cards - dynamically loaded from database.
    Publicly accessible.
    """
    # Get filter parameters
    selected_grade = request.GET.get('grade', '5')
    selected_topics = request.GET.getlist('topic', [])
    selected_location = request.GET.get('location', '')
    search_query = request.GET.get('q', '')

    if getattr(settings, 'USE_FIRESTORE', False):
        # Use Firestore for data
        activities_data = firestore_service.query_activities(
            grade=selected_grade if selected_grade else None,
            topics=selected_topics if selected_topics else None,
            location=selected_location if selected_location else None,
            search=search_query if search_query else None
        )
        activities = [FirestoreActivity.from_dict(a) for a in activities_data]

        # Get all topics from Firestore
        all_topics = firestore_service.get_all_topics()
    else:
        # Use Django ORM (fallback)
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
                if any(topic in activity_topics for topic in selected_topics):
                    filtered_activities.append(activity)
            activities = filtered_activities
        else:
            activities = list(activities)

        # Order by defined order
        if not isinstance(activities, list):
            activities = activities.order_by('order', 'activity_number')
        else:
            activities = sorted(activities, key=lambda a: (a.order, a.activity_number))

        # Get all unique topics for filter buttons
        all_activities = Activity.objects.filter(is_published=True)
        all_topics = set()
        for activity in all_activities:
            all_topics.update(activity.topics if isinstance(activity.topics, list) else [])
        all_topics = sorted(list(all_topics))

    # Get taxonomies from CMS (cached)
    taxonomies = taxonomy_service.get_all_taxonomies()

    context = {
        'activities': activities,
        'selected_grade': selected_grade,
        'selected_topics': selected_topics,
        'selected_location': selected_location,
        'search_query': search_query,
        'all_topics': all_topics,
        'grade_choices': taxonomy_service.get_grade_keys(),
        'grade_levels': taxonomies['grades'],
        'topic_taxonomies': taxonomies['topics'],
        'court_types': taxonomies['courtTypes'],
    }
    return render(request, 'home.html', context)


@login_required
def activity_detail(request, slug):
    """
    Activity detail page with prerequisites, objectives, materials, etc.
    Dynamically loaded from database. Requires authentication.
    """
    if getattr(settings, 'USE_FIRESTORE', False):
        # Use Firestore for data
        activity_data = firestore_service.get_activity_by_slug(slug)
        if not activity_data:
            raise Http404("Activity not found")

        activity = FirestoreActivity.from_dict(activity_data)

        # Get video URL from related_videos (new direct upload) or legacy video_ids
        video_url = None
        if activity.related_videos:
            # Use first related video as main video
            first_video = activity.related_videos[0]
            video_url = first_video.get('fileUrl', '')
        elif activity.video_ids:
            # Fallback to legacy video references
            videos = firestore_service.get_videos_by_ids(activity.video_ids[:1])
            if videos:
                video = FirestoreVideo.from_dict(videos[0])
                video_url = video.get_streaming_url(expiration_minutes=120)

        # Get teacher resources from direct uploads or legacy references
        teacher_resources = []
        if activity.teacher_resources:
            # Use direct upload resources (new CMS structure)
            for res in activity.teacher_resources:
                teacher_resources.append({
                    'title': res.get('title', 'Untitled'),
                    'caption': res.get('caption', ''),
                    'type': res.get('type', 'pdf'),
                    'file_url': get_storage_url(res.get('fileUrl', '')),
                })
        elif activity.teacher_resource_ids:
            # Fallback to legacy resource references
            resources_data = firestore_service.get_resources_by_ids(activity.teacher_resource_ids)
            for res_data in resources_data:
                resource = FirestoreResource.from_dict(res_data)
                teacher_resources.append({
                    'title': resource.title,
                    'caption': resource.caption,
                    'type': resource.file_type,
                    'file_url': resource.file_url,
                })

        # Get student resources from direct uploads or legacy references
        student_resources = []
        if activity.student_resources:
            # Use direct upload resources (new CMS structure)
            for res in activity.student_resources:
                student_resources.append({
                    'title': res.get('title', 'Untitled'),
                    'caption': res.get('caption', ''),
                    'type': res.get('type', 'pdf'),
                    'file_url': get_storage_url(res.get('fileUrl', '')),
                })
        elif activity.student_resource_ids:
            # Fallback to legacy resource references
            resources_data = firestore_service.get_resources_by_ids(activity.student_resource_ids)
            for res_data in resources_data:
                resource = FirestoreResource.from_dict(res_data)
                student_resources.append({
                    'title': resource.title,
                    'caption': resource.caption,
                    'type': resource.file_type,
                    'file_url': resource.file_url,
                })

        # Get related activities (same grade)
        related_data = firestore_service.query_activities(grade=activity.grade)
        related_activities = [
            FirestoreActivity.from_dict(a) for a in related_data
            if a.get('id') != activity.id
        ][:3]

    else:
        # Use Django ORM (fallback)
        activity = get_object_or_404(Activity, slug=slug, is_published=True)

        # Track view if user is authenticated and video exists
        if request.user.is_authenticated and activity.video_asset:
            try:
                session_id = request.session.session_key or 'anonymous'
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

        # Get resource download URLs
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

        # Get related activities
        related_activities = Activity.objects.filter(
            is_published=True,
            grade=activity.grade
        ).exclude(id=activity.id).order_by('order', 'activity_number')[:3]

    # Build context with all activity data
    context = {
        'activity': activity,
        'video_url': video_url,
        'teacher_resources': teacher_resources,
        'student_resources': student_resources,
        'related_activities': related_activities,
    }

    # Add new fields from Firestore adapter (if available)
    if getattr(settings, 'USE_FIRESTORE', False):
        # Transform related_videos URLs
        transformed_videos = []
        for video in (activity.related_videos or []):
            transformed_videos.append({
                'title': video.get('title', ''),
                'fileUrl': get_storage_url(video.get('fileUrl', '')),
                'thumbnailUrl': get_storage_url(video.get('thumbnailUrl', '')),
                'duration': video.get('duration', 0),
                'type': video.get('type', ''),
                'caption': video.get('caption', ''),
            })
        context['related_videos'] = transformed_videos
        context['lesson_pdf_url'] = get_storage_url(activity.lesson_pdf or '')
        context['estimated_time'] = activity.estimated_time or 0
        context['lesson_overview'] = activity.lesson_overview or []

    return render(request, 'activity_detail.html', context)


@login_required
def community(request):
    """
    Community page for teacher collaboration. Requires authentication.
    """
    return render(request, 'community.html')


def faq(request):
    """
    FAQ page. Publicly accessible.
    """
    return render(request, 'faq.html')


@login_required
def my_notes(request):
    """
    User's notes on activities
    """
    # Future implementation
    return render(request, 'notes.html')


@login_required
def search_activities(request):
    """
    AJAX endpoint for searching/filtering activities.
    Returns JSON for dynamic updates. Requires authentication.
    """
    # Get search parameters
    query = request.GET.get('q', '')
    grade = request.GET.get('grade', '')
    topics = request.GET.getlist('topic', [])
    location = request.GET.get('location', '')

    if getattr(settings, 'USE_FIRESTORE', False):
        # Use Firestore for data
        activities_data = firestore_service.query_activities(
            grade=grade if grade else None,
            topics=topics if topics else None,
            location=location if location else None,
            search=query if query else None
        )
        activities = [FirestoreActivity.from_dict(a) for a in activities_data]
    else:
        # Use Django ORM (fallback)
        activities = Activity.objects.filter(is_published=True)

        if grade:
            activities = activities.filter(grade=grade)

        if location:
            activities = activities.filter(location=location)

        if query:
            activities = activities.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query)
            )

        if topics:
            filtered_activities = []
            for activity in activities:
                activity_topics = activity.topics if isinstance(activity.topics, list) else []
                if any(topic in activity_topics for topic in topics):
                    filtered_activities.append(activity)
            activities = filtered_activities
        else:
            activities = list(activities)

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
                'topics': activity.topics if isinstance(activity.topics, list) else [],
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



























"""
Firestore Service for reading data from FireCMS
This module provides functions to sync Firestore collections to Django models
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from django.utils import timezone
from firebase_admin import firestore
import firebase_admin

logger = logging.getLogger(__name__)


def get_firestore_client():
    """Get Firestore client, initializing if needed"""
    if not firebase_admin._apps:
        from firebase_init import initialize_firebase
        initialize_firebase()
    
    return firestore.client()


def get_all_documents(collection_name: str) -> List[Dict[str, Any]]:
    """
    Get all documents from a Firestore collection
    
    Args:
        collection_name: Name of the Firestore collection
        
    Returns:
        List of documents as dictionaries with 'id' field added
    """
    try:
        db = get_firestore_client()
        docs = db.collection(collection_name).stream()
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(data)
        
        logger.info(f"Retrieved {len(results)} documents from '{collection_name}'")
        return results
        
    except Exception as e:
        logger.error(f"Error fetching documents from '{collection_name}': {e}")
        return []


def get_document(collection_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a single document from Firestore
    
    Args:
        collection_name: Name of the Firestore collection
        doc_id: Document ID
        
    Returns:
        Document data as dictionary or None if not found
    """
    try:
        db = get_firestore_client()
        doc = db.collection(collection_name).document(doc_id).get()
        
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            return data
        
        return None
        
    except Exception as e:
        logger.error(f"Error fetching document '{doc_id}' from '{collection_name}': {e}")
        return None


def get_published_activities() -> List[Dict[str, Any]]:
    """
    Get all published activities from Firestore
    
    Returns:
        List of published activities
    """
    try:
        db = get_firestore_client()
        docs = db.collection('activities').where('status', '==', 'published').stream()
        
        results = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(data)
        
        logger.info(f"Retrieved {len(results)} published activities from Firestore")
        return results
        
    except Exception as e:
        logger.error(f"Error fetching published activities: {e}")
        return []


def get_videos() -> List[Dict[str, Any]]:
    """
    Get all videos from Firestore
    
    Returns:
        List of videos
    """
    return get_all_documents('videos')


def get_resources() -> List[Dict[str, Any]]:
    """
    Get all resources from Firestore
    
    Returns:
        List of resources
    """
    return get_all_documents('resources')


def sync_videos_to_django(user, school):
    """
    Sync videos from Firestore to Django VideoAsset model
    
    Args:
        user: Django user to set as owner
        school: Django school to associate with
        
    Returns:
        Tuple of (created_count, updated_count)
    """
    from content.models import VideoAsset
    
    videos = get_videos()
    created = 0
    updated = 0
    
    for video_data in videos:
        firestore_id = video_data.get('id')
        
        # Check if video already exists (by matching title or creating a mapping)
        existing = VideoAsset.objects.filter(
            title=video_data.get('title', ''),
            school=school
        ).first()
        
        defaults = {
            'description': video_data.get('description', ''),
            'storage_uri': video_data.get('fileUrl', ''),
            'thumbnail_uri': video_data.get('thumbnailUrl', ''),
            'duration': video_data.get('duration'),
            'file_size': video_data.get('fileSize'),
            'status': 'PUBLISHED',  # Assume published in FireCMS
            'owner': user,
            'school': school,
            'grade': '5',  # Default grade
            'topic': 'fractions_basics',  # Default topic
        }
        
        if existing:
            for key, value in defaults.items():
                if value is not None:
                    setattr(existing, key, value)
            existing.save()
            updated += 1
            logger.info(f"Updated video: {existing.title}")
        else:
            video = VideoAsset.objects.create(
                title=video_data.get('title', 'Untitled Video'),
                **defaults
            )
            created += 1
            logger.info(f"Created video: {video.title}")
    
    return created, updated


def sync_resources_to_django(user, school):
    """
    Sync resources from Firestore to Django Resource model
    
    Args:
        user: Django user to set as owner
        school: Django school to associate with
        
    Returns:
        Tuple of (created_count, updated_count)
    """
    from content.models import Resource
    
    resources = get_resources()
    created = 0
    updated = 0
    
    # File type mapping from FireCMS to Django
    type_mapping = {
        'pdf': 'pdf',
        'pptx': 'pptx',
        'docx': 'docx',
        'ppt': 'ppt',
        'doc': 'doc',
    }
    
    for resource_data in resources:
        firestore_id = resource_data.get('id')
        
        existing = Resource.objects.filter(
            title=resource_data.get('title', ''),
            school=school
        ).first()
        
        file_type = resource_data.get('fileType', 'pdf')
        file_type = type_mapping.get(file_type, 'pdf')
        
        defaults = {
            'description': resource_data.get('description', ''),
            'file_uri': resource_data.get('fileUrl', ''),
            'file_type': file_type,
            'file_size': resource_data.get('fileSize'),
            'status': 'PUBLISHED',
            'owner': user,
            'school': school,
        }
        
        if existing:
            for key, value in defaults.items():
                if value is not None:
                    setattr(existing, key, value)
            existing.save()
            updated += 1
            logger.info(f"Updated resource: {existing.title}")
        else:
            resource = Resource.objects.create(
                title=resource_data.get('title', 'Untitled Resource'),
                **defaults
            )
            created += 1
            logger.info(f"Created resource: {resource.title}")
    
    return created, updated


def sync_activities_to_django(user, school):
    """
    Sync activities from Firestore to Django Activity model
    
    Args:
        user: Django user for ownership
        school: Django school to associate with
        
    Returns:
        Tuple of (created_count, updated_count)
    """
    from content.models import Activity, VideoAsset, Resource
    from django.utils.text import slugify
    
    activities = get_published_activities()
    created = 0
    updated = 0
    
    for activity_data in activities:
        firestore_id = activity_data.get('id')
        title = activity_data.get('title', 'Untitled Activity')
        slug = slugify(title)
        
        # Ensure unique slug
        base_slug = slug
        counter = 1
        while Activity.objects.filter(slug=slug).exclude(title=title).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        existing = Activity.objects.filter(slug=slug).first() or \
                   Activity.objects.filter(title=title).first()
        
        # Get grade levels - convert numbers to string format
        grade_levels = activity_data.get('gradeLevel', [5])
        grade = str(grade_levels[0]) if grade_levels else '5'
        
        # Get taxonomy
        taxonomy = activity_data.get('taxonomy', {})
        topics = [taxonomy.get('topic', '')] if taxonomy.get('topic') else []
        tags = activity_data.get('tags', [])
        topics.extend(tags)
        
        # Determine location
        court_type = taxonomy.get('courtType', '')
        location = 'court' if 'court' in court_type.lower() else 'classroom'
        
        defaults = {
            'title': title,
            'slug': slug,
            'description': activity_data.get('description', ''),
            'activity_number': len(Activity.objects.filter(grade=grade)) + 1,
            'grade': grade,
            'topics': topics,
            'location': location,
            'prerequisites': [],
            'learning_objectives': '',
            'materials': [],
            'game_rules': [],
            'key_terms': {},
            'thumbnail_uri': activity_data.get('thumbnailUrl', ''),
            'is_published': activity_data.get('status') == 'published',
            'order': 0,
        }
        
        if existing:
            for key, value in defaults.items():
                if key != 'slug' or not existing.slug:  # Don't overwrite existing slug
                    setattr(existing, key, value)
            existing.save()
            activity = existing
            updated += 1
            logger.info(f"Updated activity: {activity.title}")
        else:
            activity = Activity.objects.create(**defaults)
            created += 1
            logger.info(f"Created activity: {activity.title}")
        
        # Link videos if they exist
        videos_data = activity_data.get('videos', [])
        for video_ref in videos_data:
            if isinstance(video_ref, dict):
                video_title = video_ref.get('title', '')
                video_obj = VideoAsset.objects.filter(title=video_title, school=school).first()
                if video_obj and not activity.video_asset:
                    activity.video_asset = video_obj
                    activity.save()
        
        # Link resources if they exist
        resources_data = activity_data.get('resources', [])
        for resource_ref in resources_data:
            if isinstance(resource_ref, dict):
                resource_title = resource_ref.get('title', '')
                resource_obj = Resource.objects.filter(title=resource_title, school=school).first()
                if resource_obj:
                    activity.teacher_resources.add(resource_obj)
    
    return created, updated


def full_sync(user, school):
    """
    Perform a full sync of all Firestore content to Django
    
    Args:
        user: Django user for ownership
        school: Django school to associate with
        
    Returns:
        Dictionary with sync results
    """
    logger.info("Starting full Firestore → Django sync...")
    
    results = {
        'videos': {'created': 0, 'updated': 0},
        'resources': {'created': 0, 'updated': 0},
        'activities': {'created': 0, 'updated': 0},
    }
    
    # Sync videos first (activities reference them)
    v_created, v_updated = sync_videos_to_django(user, school)
    results['videos'] = {'created': v_created, 'updated': v_updated}
    
    # Sync resources
    r_created, r_updated = sync_resources_to_django(user, school)
    results['resources'] = {'created': r_created, 'updated': r_updated}
    
    # Sync activities last
    a_created, a_updated = sync_activities_to_django(user, school)
    results['activities'] = {'created': a_created, 'updated': a_updated}
    
    logger.info(f"Sync complete: {results}")
    return results



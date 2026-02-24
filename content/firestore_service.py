"""
Firestore Service for reading data from FireCMS
This module provides functions to sync Firestore collections to Django models
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from django.utils import timezone
from firebase_admin import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
import firebase_admin

logger = logging.getLogger(__name__)

# Singleton Firestore client - reused across all requests to avoid
# re-creating gRPC channels and re-parsing credentials on every call
_firestore_client = None
FIRESTORE_QUERY_TIMEOUT_SECONDS = 5


def get_firestore_client():
    """Get or create a singleton Firestore client with explicit database name and credentials"""
    global _firestore_client
    if _firestore_client is not None:
        return _firestore_client

    from google.cloud import firestore as gc_firestore
    from google.oauth2 import service_account
    from django.conf import settings

    # Validate Firebase config before attempting to create client
    firebase_config = settings.FIREBASE_CONFIG
    if not firebase_config.get('private_key') or len(firebase_config.get('private_key', '')) < 100:
        logger.error("Firebase credentials not configured - private_key missing or invalid")
        raise ValueError("Firebase credentials not properly configured. Check FIREBASE_PRIVATE_KEY environment variable.")

    if not firebase_config.get('client_email'):
        logger.error("Firebase credentials not configured - client_email missing")
        raise ValueError("Firebase credentials not properly configured. Check FIREBASE_CLIENT_EMAIL environment variable.")

    # Use service account credentials from Django settings
    credentials = service_account.Credentials.from_service_account_info(
        firebase_config
    )

    # Get project_id from config (not hardcoded)
    project_id = firebase_config.get('project_id', 'fractionball-lms')

    # Use google-cloud-firestore directly with explicit database='default'
    # Note: The database is named 'default' (not '(default)') in this project
    _firestore_client = gc_firestore.Client(
        project=project_id,
        database='default',
        credentials=credentials
    )
    return _firestore_client


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
        docs = db.collection(collection_name).stream(timeout=FIRESTORE_QUERY_TIMEOUT_SECONDS)
        
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
        docs = db.collection('activities').where(filter=FieldFilter('status', '==', 'published')).stream()

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


def query_activities(
    grade: Optional[str] = None,
    topics: Optional[List[str]] = None,
    location: Optional[str] = None,
    search: Optional[str] = None,
    extra_taxonomy: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """
    Query activities with filters

    Args:
        grade: Grade level (e.g., 'K', '1', '2', ... '8')
        topics: List of topic tags to filter by
        location: 'classroom', 'court', or 'both'
        search: Search query for title/description
        extra_taxonomy: Dict of additional taxonomy type->value filters
                        (e.g., {'standard': 'CCSS.3.NF.1'})

    Returns:
        List of matching activities
    """
    try:
        db = get_firestore_client()
        query = db.collection('activities').where(filter=FieldFilter('status', '==', 'published'))

        # Filter by grade level
        if grade:
            # Convert grade to number for Firestore (K=0, 1=1, etc.)
            grade_num = 0 if grade == 'K' else int(grade)
            query = query.where(filter=FieldFilter('gradeLevel', 'array_contains', grade_num))

        # Build key→label map from taxonomy data so we can match filter keys
        # against activity values (which store labels, not keys)
        key_to_label = {}
        if topics or extra_taxonomy:
            from content.taxonomy_service import get_all_taxonomy_categories
            for cat in get_all_taxonomy_categories():
                for val in cat.get('values', []):
                    key_to_label[val['key']] = val.get('label', val['key'])

        # Execute query
        docs = query.stream()
        results = []

        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id

            # Apply location filter in Python (Firestore limitation on multiple array_contains)
            if location:
                activity_location = data.get('location', '') or data.get('taxonomy', {}).get('courtType', '')
                if location == 'court' and 'court' not in activity_location.lower():
                    continue
                if location == 'classroom' and 'classroom' not in activity_location.lower():
                    continue

            # Apply topic filter in Python
            if topics:
                activity_tags = data.get('tags', [])
                activity_topic = data.get('taxonomy', {}).get('topic', '')
                all_activity_values = activity_tags + ([activity_topic] if activity_topic else [])
                # Normalize: lowercase all activity values for comparison
                all_activity_lower = [v.lower() for v in all_activity_values if v]
                # Check if any filter topic matches (by key, label, or lowercase)
                matched = False
                for t in topics:
                    t_lower = t.lower()
                    label = key_to_label.get(t, '')
                    if (t in all_activity_values
                            or t_lower in all_activity_lower
                            or label in all_activity_values
                            or label.lower() in all_activity_lower):
                        matched = True
                        break
                if not matched:
                    continue

            # Apply search filter in Python
            if search:
                search_lower = search.lower()
                title = data.get('title', '').lower()
                description = data.get('description', '').lower()
                if search_lower not in title and search_lower not in description:
                    continue

            # Apply extra taxonomy filters (auto-discovered taxonomy types)
            if extra_taxonomy:
                activity_taxonomy = data.get('taxonomy', {})
                skip = False
                for tax_type, tax_value in extra_taxonomy.items():
                    activity_tax_value = activity_taxonomy.get(tax_type, '')
                    # Resolve filter key to label for comparison
                    filter_label = key_to_label.get(tax_value, '')
                    if isinstance(activity_tax_value, list):
                        act_lower = [v.lower() for v in activity_tax_value if isinstance(v, str)]
                        if (tax_value not in activity_tax_value
                                and tax_value.lower() not in act_lower
                                and filter_label not in activity_tax_value
                                and filter_label.lower() not in act_lower):
                            skip = True
                            break
                    elif isinstance(activity_tax_value, str):
                        act_lower = activity_tax_value.lower()
                        if (tax_value.lower() != act_lower
                                and filter_label.lower() != act_lower):
                            skip = True
                            break
                    else:
                        skip = True
                        break
                if skip:
                    continue

            results.append(data)

        # Sort by order and activityNumber
        results.sort(key=lambda x: (x.get('order', 0), x.get('activityNumber', 0)))

        logger.info(f"Query returned {len(results)} activities")
        return results

    except Exception as e:
        logger.error(f"Error querying activities: {e}")
        return []


def get_activity_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """
    Get a single activity by its slug

    Args:
        slug: URL-friendly activity identifier

    Returns:
        Activity data or None if not found
    """
    try:
        db = get_firestore_client()
        docs = db.collection('activities').where(filter=FieldFilter('slug', '==', slug)).where(filter=FieldFilter('status', '==', 'published')).limit(1).stream()

        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            return data

        return None

    except Exception as e:
        logger.error(f"Error fetching activity by slug '{slug}': {e}")
        return None


def get_videos_by_ids(video_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Get multiple videos by their document IDs (single batch read)

    Args:
        video_ids: List of Firestore document IDs

    Returns:
        List of video data
    """
    if not video_ids:
        return []

    try:
        db = get_firestore_client()
        doc_refs = [db.collection('videos').document(vid) for vid in video_ids]
        docs = db.get_all(doc_refs)

        results = []
        for doc in docs:
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)

        return results

    except Exception as e:
        logger.error(f"Error fetching videos by IDs: {e}")
        return []


def get_activities_by_ids(activity_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Get multiple activities by their document IDs (single batch read)

    Args:
        activity_ids: List of Firestore document IDs

    Returns:
        List of activity data
    """
    if not activity_ids:
        return []

    try:
        db = get_firestore_client()
        doc_refs = [db.collection('activities').document(aid) for aid in activity_ids]
        docs = db.get_all(doc_refs)

        results = []
        for doc in docs:
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)

        return results

    except Exception as e:
        logger.error(f"Error fetching activities by IDs: {e}")
        return []


def get_resources_by_ids(resource_ids: List[str]) -> List[Dict[str, Any]]:
    """
    Get multiple resources by their document IDs (single batch read)

    Args:
        resource_ids: List of Firestore document IDs

    Returns:
        List of resource data
    """
    if not resource_ids:
        return []

    try:
        db = get_firestore_client()
        doc_refs = [db.collection('resources').document(rid) for rid in resource_ids]
        docs = db.get_all(doc_refs)

        results = []
        for doc in docs:
            if doc.exists:
                data = doc.to_dict()
                data['id'] = doc.id
                results.append(data)

        return results

    except Exception as e:
        logger.error(f"Error fetching resources by IDs: {e}")
        return []


def check_community_slug_exists(slug: str) -> bool:
    """
    Check if a community post with the given slug already exists.

    Args:
        slug: URL-friendly post identifier

    Returns:
        True if a post with this slug exists
    """
    try:
        db = get_firestore_client()
        docs = db.collection('communityPosts').where(
            filter=FieldFilter('slug', '==', slug)
        ).limit(1).stream()
        for doc in docs:
            return True
        return False
    except Exception as e:
        logger.error(f"Error checking slug existence: {e}")
        return False


def get_community_posts(
    limit: int = 20,
    category: Optional[str] = None,
    search: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Get recent community posts, optionally filtered.

    Args:
        limit: Maximum number of posts to return
        category: Optional category key to filter by
        search: Optional search string for title/content

    Returns:
        List of community posts
    """
    try:
        db = get_firestore_client()

        # Try with status filter + ordering (requires composite index)
        try:
            query = db.collection('communityPosts').where(
                filter=FieldFilter('status', '==', 'active')
            )
            if category:
                query = query.where(filter=FieldFilter('category', '==', category))
            query = query.order_by(
                'createdAt', direction=firestore.Query.DESCENDING
            ).limit(limit)
            docs = list(query.stream())
        except Exception as index_err:
            # Fallback: fetch without ordering, sort in Python
            logger.warning(f"Composite index may be needed, falling back to simple query: {index_err}")
            query = db.collection('communityPosts').limit(limit)
            docs = list(query.stream())

        results = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id

            # Filter by status in Python (fallback path may not have it)
            if data.get('status') and data['status'] != 'active':
                continue

            # Category filter in Python (in case Firestore filter wasn't applied)
            if category and data.get('category') != category:
                continue

            # Search filter in Python (Firestore has no full-text search)
            if search:
                search_lower = search.lower()
                title = data.get('title', '').lower()
                content = data.get('content', '').lower()
                if search_lower not in title and search_lower not in content:
                    continue

            results.append(data)

        # Sort: pinned first, then by createdAt descending
        def sort_key(x):
            created = x.get('createdAt')
            ts = created.timestamp() if hasattr(created, 'timestamp') else 0
            return (not x.get('isPinned', False), -ts)

        results.sort(key=sort_key)

        return results

    except Exception as e:
        logger.error(f"Error fetching community posts: {e}")
        return []


def get_post_with_comments(post_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a community post with its comments

    Args:
        post_id: Document ID of the post

    Returns:
        Post data with comments array, or None if not found
    """
    try:
        db = get_firestore_client()

        # Get the post
        post_doc = db.collection('communityPosts').document(post_id).get()
        if not post_doc.exists:
            return None

        post_data = post_doc.to_dict()
        post_data['id'] = post_doc.id

        # Get comments from subcollection
        comments_docs = db.collection('communityPosts').document(post_id).collection('comments').order_by('createdAt').stream()

        comments = []
        for doc in comments_docs:
            comment_data = doc.to_dict()
            comment_data['id'] = doc.id
            comments.append(comment_data)

        post_data['comments'] = comments
        return post_data

    except Exception as e:
        logger.error(f"Error fetching post with comments: {e}")
        return None


def get_community_post_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """
    Get a community post by its slug, with comments.

    Args:
        slug: URL-friendly post identifier

    Returns:
        Post data with comments array, or None if not found
    """
    try:
        db = get_firestore_client()

        # Try with slug + status filter (may need composite index)
        try:
            docs = db.collection('communityPosts').where(
                filter=FieldFilter('slug', '==', slug)
            ).where(
                filter=FieldFilter('status', '==', 'active')
            ).limit(1).stream()
            post_data = None
            for doc in docs:
                post_data = doc.to_dict()
                post_data['id'] = doc.id
                break
        except Exception:
            # Fallback: query by slug only, check status in Python
            docs = db.collection('communityPosts').where(
                filter=FieldFilter('slug', '==', slug)
            ).limit(1).stream()
            post_data = None
            for doc in docs:
                data = doc.to_dict()
                if data.get('status', 'active') == 'active':
                    post_data = data
                    post_data['id'] = doc.id
                break

        if not post_data:
            return None

        # Get comments from subcollection
        try:
            comments_docs = db.collection('communityPosts').document(
                post_data['id']
            ).collection('comments').order_by('createdAt').stream()
        except Exception:
            # Fallback: fetch without ordering
            comments_docs = db.collection('communityPosts').document(
                post_data['id']
            ).collection('comments').stream()

        comments = []
        for doc in comments_docs:
            comment_data = doc.to_dict()
            comment_data['id'] = doc.id
            comments.append(comment_data)

        post_data['comments'] = comments
        return post_data

    except Exception as e:
        logger.error(f"Error fetching post by slug '{slug}': {e}")
        return None


def increment_post_view_count(post_id: str) -> bool:
    """
    Increment the view count for a community post.

    Args:
        post_id: Firestore document ID

    Returns:
        True if successful
    """
    try:
        db = get_firestore_client()
        db.collection('communityPosts').document(post_id).update({
            'viewCount': firestore.Increment(1)
        })
        return True
    except Exception as e:
        logger.error(f"Error incrementing view count for post {post_id}: {e}")
        return False


def get_faqs_by_category(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Get FAQs, optionally filtered by category

    Args:
        category: Optional category filter

    Returns:
        List of FAQ entries
    """
    try:
        db = get_firestore_client()
        # Query without order_by to avoid composite index requirement; sort in Python
        query = db.collection('faqs').where(filter=FieldFilter('status', '==', 'published'))

        if category:
            query = query.where(filter=FieldFilter('category', '==', category))

        docs = query.stream()

        results = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            results.append(data)

        # Sort by displayOrder in Python
        results.sort(key=lambda x: x.get('displayOrder', 0))

        return results

    except Exception as e:
        logger.error(f"Error fetching FAQs: {e}")
        return []


def get_all_topics() -> List[str]:
    """
    Get all unique topics from published activities

    Returns:
        Sorted list of unique topic strings
    """
    try:
        activities = get_published_activities()
        all_topics = set()

        for activity in activities:
            tags = activity.get('tags', [])
            topic = activity.get('taxonomy', {}).get('topic')
            all_topics.update(tags)
            if topic:
                all_topics.add(topic)

        return sorted(list(all_topics))

    except Exception as e:
        logger.error(f"Error fetching topics: {e}")
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


# =============================================================================
# Firestore Write Functions (Django → Firestore sync)
# =============================================================================

def get_user_role(firebase_uid: str) -> Optional[str]:
    """
    Get user role from Firestore users collection.

    This is the single source of truth for user roles.
    Called on login to sync role from Firestore to Django.

    Args:
        firebase_uid: Firebase user ID (document ID in users collection)

    Returns:
        Role string (ADMIN, CONTENT_MANAGER, REGISTERED_USER) or None if not found
    """
    try:
        user_doc = get_document('users', firebase_uid)
        if user_doc:
            return user_doc.get('role')
        return None
    except Exception as e:
        logger.error(f"Error fetching user role from Firestore: {e}")
        return None


def create_or_update_user_profile(firebase_uid: str, user_data: Dict[str, Any]) -> bool:
    """
    Write/update user profile to Firestore users collection

    Args:
        firebase_uid: Firebase user ID (used as document ID)
        user_data: Dictionary with user profile data

    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_firestore_client()
        db.collection('users').document(firebase_uid).set(user_data, merge=True)
        logger.info(f"Synced user profile to Firestore: {firebase_uid}")
        return True
    except Exception as e:
        logger.error(f"Failed to sync user profile to Firestore: {e}")
        return False


def create_community_post(post_id: str, post_data: Dict[str, Any]) -> bool:
    """
    Create a community post in Firestore

    Args:
        post_id: Django post ID (used as document ID)
        post_data: Dictionary with post data

    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_firestore_client()
        db.collection('communityPosts').document(str(post_id)).set(post_data)
        logger.info(f"Created community post in Firestore: {post_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to create community post in Firestore: {e}")
        return False


def add_comment_to_post(post_id: str, comment_id: str, comment_data: Dict[str, Any]) -> bool:
    """
    Add comment to Firestore post's comments subcollection

    Args:
        post_id: Django post ID
        comment_id: Django comment ID (used as document ID)
        comment_data: Dictionary with comment data

    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_firestore_client()
        db.collection('communityPosts').document(str(post_id)).collection('comments').document(str(comment_id)).set(comment_data)
        logger.info(f"Added comment {comment_id} to post {post_id} in Firestore")
        return True
    except Exception as e:
        logger.error(f"Failed to add comment to Firestore: {e}")
        return False


def update_community_post(post_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update existing Firestore community post

    Args:
        post_id: Django post ID
        updates: Dictionary with fields to update

    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_firestore_client()
        db.collection('communityPosts').document(str(post_id)).update(updates)
        logger.info(f"Updated community post in Firestore: {post_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to update community post in Firestore: {e}")
        return False


def delete_community_post(post_id: str) -> bool:
    """
    Delete post from Firestore

    Args:
        post_id: Django post ID

    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_firestore_client()
        # Delete all comments in subcollection first
        comments_ref = db.collection('communityPosts').document(str(post_id)).collection('comments')
        for comment in comments_ref.stream():
            comment.reference.delete()
        # Delete the post document
        db.collection('communityPosts').document(str(post_id)).delete()
        logger.info(f"Deleted community post from Firestore: {post_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete community post from Firestore: {e}")
        return False


def delete_comment(post_id: str, comment_id: str) -> bool:
    """
    Soft delete comment in Firestore (mark as deleted)

    Args:
        post_id: Django post ID
        comment_id: Django comment ID

    Returns:
        True if successful, False otherwise
    """
    try:
        db = get_firestore_client()
        db.collection('communityPosts').document(str(post_id)).collection('comments').document(str(comment_id)).update({'isDeleted': True})
        logger.info(f"Soft deleted comment {comment_id} in Firestore")
        return True
    except Exception as e:
        logger.error(f"Failed to delete comment from Firestore: {e}")
        return False


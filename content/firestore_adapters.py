"""
Firestore Data Adapters

These adapter classes convert Firestore documents to objects
that are compatible with Django templates (mimicking Django model interfaces).
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class FirestoreActivity:
    """
    Adapter class that mirrors Django Activity model interface.
    Allows Firestore data to be used directly in templates.
    """
    id: str
    title: str
    slug: str
    description: str
    grade: str
    activity_number: int
    topics: List[str] = field(default_factory=list)
    location: str = 'classroom'
    icon_type: str = 'cone'
    prerequisites: List[str] = field(default_factory=list)
    learning_objectives: List[str] = field(default_factory=list)  # Changed to list
    materials: List[str] = field(default_factory=list)
    game_rules: List[str] = field(default_factory=list)
    key_terms: Dict[str, str] = field(default_factory=dict)
    thumbnail_url: str = ''
    order: int = 0
    # New fields for direct uploads
    estimated_time: int = 0  # in minutes
    lesson_overview: List[Dict[str, Any]] = field(default_factory=list)
    related_videos: List[Dict[str, Any]] = field(default_factory=list)
    teacher_resources: List[Dict[str, Any]] = field(default_factory=list)
    student_resources: List[Dict[str, Any]] = field(default_factory=list)
    lesson_pdf: str = ''
    # Legacy fields (kept for backward compatibility)
    video_ids: List[str] = field(default_factory=list)
    teacher_resource_ids: List[str] = field(default_factory=list)
    student_resource_ids: List[str] = field(default_factory=list)
    # For template compatibility
    _video_asset: Any = None

    @property
    def topic_tags(self) -> List[str]:
        """Return topics as a list for template rendering"""
        return self.topics if isinstance(self.topics, list) else []

    @property
    def video_asset(self) -> Optional[Any]:
        """Return video asset for template compatibility"""
        return self._video_asset

    def get_location_display(self) -> str:
        """Return human-readable location name"""
        location_map = {
            'classroom': 'Classroom',
            'court': 'Court',
            'both': 'Both',
        }
        return location_map.get(self.location, self.location.title())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FirestoreActivity':
        """
        Create a FirestoreActivity from a Firestore document dict.

        Args:
            data: Firestore document data (with 'id' field added)

        Returns:
            FirestoreActivity instance
        """
        # Extract grade level - convert from number to string format
        grade_levels = data.get('gradeLevel', [])
        if grade_levels:
            grade_num = grade_levels[0] if isinstance(grade_levels, list) else grade_levels
            grade = 'K' if grade_num == 0 else str(grade_num)
        else:
            grade = '5'  # Default

        # Extract location from taxonomy
        taxonomy = data.get('taxonomy', {})
        court_type = taxonomy.get('courtType', '')
        if 'court' in court_type.lower():
            location = 'court'
        elif 'classroom' in court_type.lower():
            location = 'classroom'
        else:
            location = data.get('location', 'both')

        # Extract topics from tags and taxonomy
        topics = list(data.get('tags', []))
        topic_from_taxonomy = taxonomy.get('topic')
        if topic_from_taxonomy and topic_from_taxonomy not in topics:
            topics.insert(0, topic_from_taxonomy)

        # Extract video IDs from videos array
        video_ids = []
        for video_ref in data.get('videos', []):
            if isinstance(video_ref, dict):
                video_id = video_ref.get('videoId')
                if video_id:
                    # Handle Firestore DocumentReference
                    if hasattr(video_id, 'id'):
                        video_ids.append(video_id.id)
                    elif isinstance(video_id, str):
                        video_ids.append(video_id)

        # Extract resource IDs
        teacher_resource_ids = []
        student_resource_ids = []
        for resource_ref in data.get('resources', []):
            if isinstance(resource_ref, dict):
                resource_id = resource_ref.get('resourceId')
                resource_type = resource_ref.get('type', 'teacher')
                if resource_id:
                    rid = resource_id.id if hasattr(resource_id, 'id') else resource_id
                    if resource_type == 'student':
                        student_resource_ids.append(rid)
                    else:
                        teacher_resource_ids.append(rid)

        # Extract direct upload fields (new CMS structure)
        related_videos = data.get('relatedVideos', []) or []
        teacher_resources = data.get('teacherResources', []) or []
        student_resources = data.get('studentResources', []) or []
        lesson_pdf = data.get('lessonPdf', '') or ''
        estimated_time = data.get('estimatedTime', 0) or 0
        lesson_overview = data.get('lessonOverview', []) or []

        # Handle learningObjectives - can be string or array
        learning_objectives_raw = data.get('learningObjectives', [])
        if isinstance(learning_objectives_raw, str):
            learning_objectives = [learning_objectives_raw] if learning_objectives_raw else []
        else:
            learning_objectives = learning_objectives_raw or []

        return cls(
            id=data.get('id', ''),
            title=data.get('title', 'Untitled Activity'),
            slug=data.get('slug', ''),
            description=data.get('description', ''),
            grade=grade,
            activity_number=data.get('activityNumber', 1),
            topics=topics,
            location=location,
            icon_type=data.get('iconType', 'cone'),
            prerequisites=data.get('prerequisites', []),
            learning_objectives=learning_objectives,
            materials=data.get('materials', []),
            game_rules=data.get('gameRules', []),
            key_terms=data.get('keyTerms', {}),
            thumbnail_url=data.get('thumbnailUrl', ''),
            order=data.get('order', 0),
            # New direct upload fields
            estimated_time=estimated_time,
            lesson_overview=lesson_overview,
            related_videos=related_videos,
            teacher_resources=teacher_resources,
            student_resources=student_resources,
            lesson_pdf=lesson_pdf,
            # Legacy fields
            video_ids=video_ids,
            teacher_resource_ids=teacher_resource_ids,
            student_resource_ids=student_resource_ids,
        )


@dataclass
class FirestoreVideo:
    """
    Adapter class for Firestore video documents.
    """
    id: str
    title: str
    description: str = ''
    file_url: str = ''
    thumbnail_url: str = ''
    duration: int = 0  # in seconds
    file_size: int = 0  # in bytes

    def get_streaming_url(self, expiration_minutes: int = 120) -> str:
        """
        Generate a streaming URL for the video.

        Args:
            expiration_minutes: URL expiration time (for signed URLs)

        Returns:
            Streaming URL string
        """
        # For Firebase Storage URLs, we may need to generate signed URLs
        # For now, return the file_url directly
        # TODO: Implement signed URL generation via firebase_storage.py
        return self.file_url

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FirestoreVideo':
        """Create a FirestoreVideo from a Firestore document dict."""
        return cls(
            id=data.get('id', ''),
            title=data.get('title', 'Untitled Video'),
            description=data.get('description', ''),
            file_url=data.get('fileUrl', ''),
            thumbnail_url=data.get('thumbnailUrl', ''),
            duration=data.get('duration', 0),
            file_size=data.get('fileSize', 0),
        )


@dataclass
class FirestoreResource:
    """
    Adapter class for Firestore resource documents.
    """
    id: str
    title: str
    caption: str = ''
    file_type: str = 'pdf'
    file_url: str = ''
    file_name: str = ''
    file_size: int = 0

    @property
    def get_file_type_display(self) -> str:
        """Return human-readable file type"""
        type_map = {
            'pdf': 'PDF',
            'pptx': 'PowerPoint',
            'docx': 'Word Document',
            'xlsx': 'Excel Spreadsheet',
        }
        return type_map.get(self.file_type, self.file_type.upper())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FirestoreResource':
        """Create a FirestoreResource from a Firestore document dict."""
        return cls(
            id=data.get('id', ''),
            title=data.get('title', 'Untitled Resource'),
            caption=data.get('caption', ''),
            file_type=data.get('type', 'pdf'),
            file_url=data.get('fileUrl', ''),
            file_name=data.get('fileName', ''),
            file_size=data.get('fileSize', 0),
        )


@dataclass
class FirestoreCommunityPost:
    """
    Adapter class for Firestore community post documents.
    """
    id: str
    title: str
    content: str = ''
    category: str = ''
    tags: List[str] = field(default_factory=list)
    author_id: str = ''
    author_name: str = ''
    is_pinned: bool = False
    view_count: int = 0
    comment_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    comments: List['FirestoreComment'] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FirestoreCommunityPost':
        """Create a FirestoreCommunityPost from a Firestore document dict."""
        # Parse comments if included
        comments = []
        for comment_data in data.get('comments', []):
            comments.append(FirestoreComment.from_dict(comment_data))

        # Handle Firestore Timestamp
        created_at = data.get('createdAt')
        if hasattr(created_at, 'isoformat'):
            created_at = created_at
        elif isinstance(created_at, dict):
            # Firestore timestamp format
            created_at = None

        return cls(
            id=data.get('id', ''),
            title=data.get('title', ''),
            content=data.get('content', ''),
            category=data.get('category', ''),
            tags=data.get('tags', []),
            author_id=data.get('authorId', ''),
            author_name=data.get('authorName', 'Anonymous'),
            is_pinned=data.get('isPinned', False),
            view_count=data.get('viewCount', 0),
            comment_count=data.get('commentCount', 0),
            created_at=created_at,
            comments=comments,
        )


@dataclass
class FirestoreComment:
    """
    Adapter class for Firestore comment documents (subcollection).
    """
    id: str
    content: str = ''
    author_id: str = ''
    author_name: str = ''
    created_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FirestoreComment':
        """Create a FirestoreComment from a Firestore document dict."""
        return cls(
            id=data.get('id', ''),
            content=data.get('content', ''),
            author_id=data.get('authorId', ''),
            author_name=data.get('authorName', 'Anonymous'),
            created_at=data.get('createdAt'),
        )


@dataclass
class FirestoreFAQ:
    """
    Adapter class for Firestore FAQ documents.
    """
    id: str
    question: str
    answer: str = ''
    category: str = ''
    display_order: int = 0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FirestoreFAQ':
        """Create a FirestoreFAQ from a Firestore document dict."""
        return cls(
            id=data.get('id', ''),
            question=data.get('question', ''),
            answer=data.get('answer', ''),
            category=data.get('category', ''),
            display_order=data.get('displayOrder', 0),
        )

"""
Django filters for content models
"""
import django_filters
from django.db import models
from .models import VideoAsset, Resource, GRADE_CHOICES, TOPIC_CHOICES


class VideoAssetFilter(django_filters.FilterSet):
    """Advanced filtering for VideoAsset model"""
    
    # Text search across title and description
    search = django_filters.CharFilter(method='filter_search', label='Search')
    
    # Taxonomy filters
    grade = django_filters.ChoiceFilter(choices=GRADE_CHOICES, empty_label="All Grades")
    topic = django_filters.ChoiceFilter(choices=TOPIC_CHOICES, empty_label="All Topics")
    
    # Tag filtering (JSON field)
    tags = django_filters.CharFilter(method='filter_tags', label='Tags')
    
    # Owner and status filters
    owner = django_filters.ModelChoiceFilter(
        queryset=None,  # Will be set dynamically
        empty_label="All Teachers"
    )
    status = django_filters.ChoiceFilter(
        choices=[('PUBLISHED', 'Published'), ('DRAFT', 'Draft'), ('PENDING', 'Pending Review')],
        empty_label="All Statuses"
    )
    
    # Duration range filters
    min_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='gte', label='Min Duration (seconds)')
    max_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='lte', label='Max Duration (seconds)')
    
    # Date range filters
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte', label='Created After')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte', label='Created Before')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('updated_at', 'updated_at'),
            ('title', 'title'),
            ('duration', 'duration'),
            ('grade', 'grade'),
        ),
        field_labels={
            'created_at': 'Date Created',
            'updated_at': 'Date Updated',
            'title': 'Title',
            'duration': 'Duration',
            'grade': 'Grade Level',
        }
    )
    
    class Meta:
        model = VideoAsset
        fields = []  # We define all fields explicitly above
    
    def __init__(self, *args, **kwargs):
        # Get the request to scope owner choices to current school
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if request and hasattr(request.user, 'school'):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            # Only show teachers from the same school
            self.filters['owner'].queryset = User.objects.filter(
                school=request.user.school,
                role__in=['TEACHER', 'SCHOOL_ADMIN']
            ).order_by('last_name', 'first_name')
    
    def filter_search(self, queryset, name, value):
        """Filter by search term in title and description"""
        if not value:
            return queryset
        
        # Use PostgreSQL full-text search if available, otherwise use icontains
        try:
            from django.contrib.postgres.search import SearchVector
            return queryset.annotate(
                search=SearchVector('title', 'description')
            ).filter(search=value)
        except ImportError:
            # Fallback for non-PostgreSQL databases
            return queryset.filter(
                models.Q(title__icontains=value) | 
                models.Q(description__icontains=value)
            )
    
    def filter_tags(self, queryset, name, value):
        """Filter by tags (JSON field)"""
        if not value:
            return queryset
        
        # Split comma-separated tags
        tags = [tag.strip().lower() for tag in value.split(',') if tag.strip()]
        if not tags:
            return queryset
        
        # Filter videos that contain any of the specified tags
        query = models.Q()
        for tag in tags:
            query |= models.Q(tags__icontains=tag)
        
        return queryset.filter(query)


class ResourceFilter(django_filters.FilterSet):
    """Advanced filtering for Resource model"""
    
    # Text search
    search = django_filters.CharFilter(method='filter_search', label='Search')
    
    # File type filter
    file_type = django_filters.ChoiceFilter(
        choices=[
            ('pdf', 'PDF Documents'),
            ('doc', 'Word Documents'),
            ('docx', 'Word Documents (DOCX)'),
            ('ppt', 'PowerPoint'),
            ('pptx', 'PowerPoint (PPTX)'),
            ('xls', 'Excel'),
            ('xlsx', 'Excel (XLSX)'),
            ('txt', 'Text Files'),
            ('image', 'Images'),
            ('other', 'Other'),
        ],
        empty_label="All File Types"
    )
    
    # Taxonomy filters (optional for resources)
    grade = django_filters.ChoiceFilter(choices=GRADE_CHOICES, empty_label="All Grades")
    topic = django_filters.ChoiceFilter(choices=TOPIC_CHOICES, empty_label="All Topics")
    
    # Tag filtering
    tags = django_filters.CharFilter(method='filter_tags', label='Tags')
    
    # Owner and status filters
    owner = django_filters.ModelChoiceFilter(
        queryset=None,  # Will be set dynamically
        empty_label="All Teachers"
    )
    status = django_filters.ChoiceFilter(
        choices=[('PUBLISHED', 'Published'), ('DRAFT', 'Draft')],
        empty_label="All Statuses"
    )
    
    # Date range filters
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte', label='Created After')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte', label='Created Before')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created_at'),
            ('title', 'title'),
            ('file_type', 'file_type'),
            ('file_size', 'file_size'),
        ),
        field_labels={
            'created_at': 'Date Created',
            'title': 'Title',
            'file_type': 'File Type',
            'file_size': 'File Size',
        }
    )
    
    class Meta:
        model = Resource
        fields = []
    
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        if request and hasattr(request.user, 'school'):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            self.filters['owner'].queryset = User.objects.filter(
                school=request.user.school,
                role__in=['TEACHER', 'SCHOOL_ADMIN']
            ).order_by('last_name', 'first_name')
    
    def filter_search(self, queryset, name, value):
        """Filter by search term in title and description"""
        if not value:
            return queryset
        
        try:
            from django.contrib.postgres.search import SearchVector
            return queryset.annotate(
                search=SearchVector('title', 'description')
            ).filter(search=value)
        except ImportError:
            return queryset.filter(
                models.Q(title__icontains=value) | 
                models.Q(description__icontains=value)
            )
    
    def filter_tags(self, queryset, name, value):
        """Filter by tags (JSON field)"""
        if not value:
            return queryset
        
        tags = [tag.strip().lower() for tag in value.split(',') if tag.strip()]
        if not tags:
            return queryset
        
        query = models.Q()
        for tag in tags:
            query |= models.Q(tags__icontains=tag)
        
        return queryset.filter(query)


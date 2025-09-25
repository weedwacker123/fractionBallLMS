from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import VideoAsset, Resource, Playlist, PlaylistItem


@admin.register(VideoAsset)
class VideoAssetAdmin(admin.ModelAdmin):
    """Admin configuration for VideoAsset model"""
    
    list_display = [
        'title', 'grade', 'topic', 'owner', 'school', 'status', 
        'duration_display', 'file_size_display', 'created_at'
    ]
    list_filter = [
        'grade', 'topic', 'status', 'school', 'created_at',
        ('owner', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['title', 'description', 'tags']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'duration_formatted', 
        'file_size_formatted', 'storage_uri_link'
    ]
    
    fieldsets = (
        (None, {
            'fields': ('id', 'title', 'description')
        }),
        ('Taxonomy', {
            'fields': ('grade', 'topic', 'tags'),
            'classes': ('collapse',)
        }),
        ('Video Information', {
            'fields': ('duration', 'duration_formatted', 'file_size', 'file_size_formatted'),
            'classes': ('collapse',)
        }),
        ('Storage', {
            'fields': ('storage_uri', 'storage_uri_link', 'thumbnail_uri'),
            'classes': ('collapse',)
        }),
        ('Organization', {
            'fields': ('owner', 'school')
        }),
        ('Workflow', {
            'fields': ('status', 'submitted_at', 'reviewed_by', 'reviewed_at', 'review_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom admin actions
    actions = ['approve_videos', 'reject_videos', 'publish_videos']
    
    def duration_display(self, obj):
        """Display formatted duration"""
        return obj.duration_formatted
    duration_display.short_description = 'Duration'
    
    def file_size_display(self, obj):
        """Display formatted file size"""
        return obj.file_size_formatted
    file_size_display.short_description = 'File Size'
    
    def storage_uri_link(self, obj):
        """Display storage URI as clickable link"""
        if obj.storage_uri:
            return format_html(
                '<a href="{}" target="_blank">View File</a>',
                obj.storage_uri
            )
        return "No file"
    storage_uri_link.short_description = 'Storage Link'
    
    def get_queryset(self, request):
        """Optimize queryset and apply school-based filtering"""
        queryset = super().get_queryset(request).select_related('owner', 'school', 'reviewed_by')
        
        # School admins can only see videos from their school
        if not request.user.is_superuser and hasattr(request.user, 'role'):
            if request.user.role == 'SCHOOL_ADMIN':
                queryset = queryset.filter(school=request.user.school)
        
        return queryset
    
    def approve_videos(self, request, queryset):
        """Bulk approve videos"""
        updated = queryset.update(
            status='PUBLISHED',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} videos approved successfully.')
    approve_videos.short_description = "Approve selected videos"
    
    def reject_videos(self, request, queryset):
        """Bulk reject videos"""
        updated = queryset.update(
            status='REJECTED',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} videos rejected.')
    reject_videos.short_description = "Reject selected videos"
    
    def publish_videos(self, request, queryset):
        """Bulk publish videos"""
        updated = queryset.update(status='PUBLISHED')
        self.message_user(request, f'{updated} videos published.')
    publish_videos.short_description = "Publish selected videos"


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    """Admin configuration for Resource model"""
    
    list_display = [
        'title', 'file_type', 'grade', 'topic', 'owner', 'school', 
        'status', 'file_size_display', 'created_at'
    ]
    list_filter = [
        'file_type', 'grade', 'topic', 'status', 'school', 'created_at',
        ('owner', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['title', 'description', 'tags']
    readonly_fields = ['id', 'created_at', 'updated_at', 'file_size_formatted', 'file_uri_link']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'title', 'description')
        }),
        ('File Information', {
            'fields': ('file_uri', 'file_uri_link', 'file_type', 'file_size', 'file_size_formatted')
        }),
        ('Taxonomy', {
            'fields': ('grade', 'topic', 'tags'),
            'classes': ('collapse',)
        }),
        ('Organization', {
            'fields': ('owner', 'school', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        """Display formatted file size"""
        return obj.file_size_formatted
    file_size_display.short_description = 'File Size'
    
    def file_uri_link(self, obj):
        """Display file URI as clickable link"""
        if obj.file_uri:
            return format_html(
                '<a href="{}" target="_blank">Download File</a>',
                obj.file_uri
            )
        return "No file"
    file_uri_link.short_description = 'File Link'
    
    def get_queryset(self, request):
        """Apply school-based filtering"""
        queryset = super().get_queryset(request).select_related('owner', 'school')
        
        # School admins can only see resources from their school
        if not request.user.is_superuser and hasattr(request.user, 'role'):
            if request.user.role == 'SCHOOL_ADMIN':
                queryset = queryset.filter(school=request.user.school)
        
        return queryset


class PlaylistItemInline(admin.TabularInline):
    """Inline admin for playlist items"""
    model = PlaylistItem
    extra = 0
    readonly_fields = ['id', 'created_at']
    fields = ['video_asset', 'order', 'notes', 'created_at']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('video_asset')


@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    """Admin configuration for Playlist model"""
    
    list_display = [
        'name', 'owner', 'school', 'video_count_display', 
        'total_duration_display', 'is_public', 'updated_at'
    ]
    list_filter = [
        'is_public', 'school', 'created_at',
        ('owner', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = ['name', 'description']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'video_count', 
        'total_duration_formatted'
    ]
    inlines = [PlaylistItemInline]
    
    fieldsets = (
        (None, {
            'fields': ('id', 'name', 'description')
        }),
        ('Settings', {
            'fields': ('is_public',)
        }),
        ('Organization', {
            'fields': ('owner', 'school')
        }),
        ('Statistics', {
            'fields': ('video_count', 'total_duration_formatted'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def video_count_display(self, obj):
        """Display video count"""
        return obj.video_count
    video_count_display.short_description = 'Videos'
    
    def total_duration_display(self, obj):
        """Display total duration"""
        return obj.total_duration_formatted
    total_duration_display.short_description = 'Total Duration'
    
    def get_queryset(self, request):
        """Apply school-based filtering and optimize"""
        queryset = super().get_queryset(request).select_related('owner', 'school')
        
        # School admins can only see playlists from their school
        if not request.user.is_superuser and hasattr(request.user, 'role'):
            if request.user.role == 'SCHOOL_ADMIN':
                queryset = queryset.filter(school=request.user.school)
        
        return queryset


@admin.register(PlaylistItem)
class PlaylistItemAdmin(admin.ModelAdmin):
    """Admin configuration for PlaylistItem model"""
    
    list_display = ['playlist', 'order', 'video_asset', 'created_at']
    list_filter = [
        ('playlist', admin.RelatedOnlyFieldListFilter),
        ('video_asset', admin.RelatedOnlyFieldListFilter),
        'created_at',
    ]
    search_fields = ['playlist__name', 'video_asset__title', 'notes']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'playlist', 'video_asset', 'order')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('playlist', 'video_asset')
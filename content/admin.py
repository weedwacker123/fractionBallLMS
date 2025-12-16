from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import (
    VideoAsset, Resource, Playlist, PlaylistItem, PlaylistShare,
    AuditLog, AssetView, AssetDownload, DailyAssetStats,
    Activity, ForumCategory, ForumPost, ForumComment
)


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


@admin.register(PlaylistShare)
class PlaylistShareAdmin(admin.ModelAdmin):
    """Admin configuration for PlaylistShare model"""
    
    list_display = ['playlist', 'created_by', 'share_token', 'is_active', 'is_expired_display', 'view_count', 'created_at']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['playlist__name', 'created_by__username', 'created_by__email']
    readonly_fields = ['id', 'share_token', 'created_at', 'updated_at', 'is_expired', 'is_valid', 'share_url_display']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'playlist', 'created_by', 'share_token')
        }),
        ('Settings', {
            'fields': ('is_active', 'expires_at')
        }),
        ('Tracking', {
            'fields': ('view_count', 'last_accessed'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_expired', 'is_valid', 'share_url_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_expired_display(self, obj):
        """Display expiration status"""
        if obj.is_expired:
            return format_html('<span style="color: red;">Expired</span>')
        elif obj.expires_at:
            return format_html('<span style="color: orange;">Expires {}</span>', obj.expires_at)
        else:
            return format_html('<span style="color: green;">Never expires</span>')
    is_expired_display.short_description = 'Expiration Status'
    
    def share_url_display(self, obj):
        """Display share URL"""
        return format_html('<a href="/api/shared/{}/" target="_blank">View Share</a>', obj.share_token)
    share_url_display.short_description = 'Share URL'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('playlist', 'created_by')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin configuration for AuditLog model"""
    
    list_display = ['action', 'user', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'user__email', 'metadata', 'ip_address']
    readonly_fields = ['id', 'created_at', 'metadata_display']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'action', 'user', 'created_at')
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata_display',),
            'classes': ('collapse',)
        }),
    )
    
    def metadata_display(self, obj):
        """Display formatted metadata"""
        import json
        if obj.metadata:
            return format_html('<pre>{}</pre>', json.dumps(obj.metadata, indent=2))
        return 'No metadata'
    metadata_display.short_description = 'Metadata'
    
    def get_queryset(self, request):
        """Optimize queryset and limit results"""
        return super().get_queryset(request).select_related('user')[:1000]  # Limit for performance


@admin.register(AssetView)
class AssetViewAdmin(admin.ModelAdmin):
    """Admin configuration for AssetView model"""
    
    list_display = ['asset', 'user', 'completion_percentage', 'duration_watched', 'viewed_at']
    list_filter = ['viewed_at', 'completion_percentage']
    search_fields = ['asset__title', 'user__username', 'session_id']
    readonly_fields = ['id', 'viewed_at']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'asset', 'user', 'session_id', 'viewed_at')
        }),
        ('Viewing Data', {
            'fields': ('duration_watched', 'completion_percentage', 'referrer')
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset and limit results"""
        return super().get_queryset(request).select_related('asset', 'user')[:1000]


@admin.register(AssetDownload)
class AssetDownloadAdmin(admin.ModelAdmin):
    """Admin configuration for AssetDownload model"""
    
    list_display = ['resource', 'user', 'download_completed', 'file_size_display', 'downloaded_at']
    list_filter = ['download_completed', 'downloaded_at']
    search_fields = ['resource__title', 'user__username']
    readonly_fields = ['id', 'downloaded_at', 'file_size_display']
    
    fieldsets = (
        (None, {
            'fields': ('id', 'resource', 'user', 'downloaded_at')
        }),
        ('Download Data', {
            'fields': ('file_size', 'file_size_display', 'download_completed')
        }),
        ('Context', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        """Display formatted file size"""
        if obj.file_size:
            if obj.file_size < 1024 * 1024:
                return f"{obj.file_size / 1024:.1f} KB"
            else:
                return f"{obj.file_size / (1024 * 1024):.1f} MB"
        return "Unknown"
    file_size_display.short_description = 'File Size'
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('resource', 'user')


@admin.register(DailyAssetStats)
class DailyAssetStatsAdmin(admin.ModelAdmin):
    """Admin configuration for DailyAssetStats model"""
    
    list_display = ['asset', 'date', 'view_count', 'unique_viewers', 'avg_completion_rate', 'playlist_adds']
    list_filter = ['date', 'view_count', 'unique_viewers']
    search_fields = ['asset__title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('asset', 'date')
        }),
        ('View Statistics', {
            'fields': ('view_count', 'unique_viewers', 'total_watch_time', 'avg_completion_rate')
        }),
        ('Engagement', {
            'fields': ('playlist_adds',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('asset')


# ============================================================================
# ACTIVITY MANAGEMENT (FireCMS-like functionality for Activities)
# ============================================================================

@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    """
    Admin configuration for Activity model
    This provides FireCMS-like content management for educational activities
    """
    
    list_display = [
        'title', 'activity_number', 'grade', 'location', 'icon_type',
        'has_video', 'resource_count', 'is_published', 'order', 'updated_at'
    ]
    list_filter = [
        'grade', 'location', 'is_published', 'icon_type', 'created_at'
    ]
    search_fields = ['title', 'slug', 'description', 'learning_objectives']
    readonly_fields = ['id', 'created_at', 'updated_at', 'topic_tags_display']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['teacher_resources', 'student_resources']
    
    # Actions for bulk operations
    actions = ['publish_activities', 'unpublish_activities', 'duplicate_activities']
    
    fieldsets = (
        ('📚 Basic Information', {
            'fields': ('id', 'title', 'slug', 'description'),
            'description': 'Core activity details'
        }),
        ('🎯 Activity Metadata', {
            'fields': ('activity_number', 'grade', 'location', 'order'),
            'description': 'Grade level and activity sequencing'
        }),
        ('📋 Topics & Tags', {
            'fields': ('topics', 'topic_tags_display'),
            'description': 'Fraction topics covered by this activity (JSON array format: ["Mixed Denominators", "Equivalent Fractions"])'
        }),
        ('📖 Learning Content', {
            'fields': ('prerequisites', 'learning_objectives', 'materials', 'game_rules', 'key_terms'),
            'classes': ('collapse',),
            'description': 'Detailed activity content - all fields support JSON format'
        }),
        ('🎬 Media & Resources', {
            'fields': ('video_asset', 'teacher_resources', 'student_resources'),
            'description': 'Attach videos and downloadable resources'
        }),
        ('🎨 Display Settings', {
            'fields': ('icon_type', 'thumbnail_uri'),
            'classes': ('collapse',),
            'description': 'Visual display options'
        }),
        ('⚙️ Publishing', {
            'fields': ('is_published',),
            'description': 'Control activity visibility'
        }),
        ('📅 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_video(self, obj):
        """Display if activity has a video attached"""
        if obj.video_asset:
            return format_html('<span style="color: green;">✅ Yes</span>')
        return format_html('<span style="color: gray;">❌ No</span>')
    has_video.short_description = 'Video'
    
    def resource_count(self, obj):
        """Display count of attached resources"""
        teacher_count = obj.teacher_resources.count()
        student_count = obj.student_resources.count()
        total = teacher_count + student_count
        if total > 0:
            return format_html('<span style="color: green;">{}</span>', total)
        return format_html('<span style="color: gray;">0</span>')
    resource_count.short_description = 'Resources'
    
    def topic_tags_display(self, obj):
        """Display topics as formatted tags"""
        if obj.topics:
            tags = obj.topics if isinstance(obj.topics, list) else []
            html_tags = ' '.join([
                f'<span style="background: #fef3c7; color: #92400e; padding: 2px 8px; '
                f'border-radius: 4px; margin: 2px; display: inline-block;">{tag}</span>'
                for tag in tags
            ])
            return format_html(html_tags) if html_tags else 'No topics'
        return 'No topics'
    topic_tags_display.short_description = 'Topic Tags'
    
    def publish_activities(self, request, queryset):
        """Bulk publish activities"""
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} activities published successfully.')
    publish_activities.short_description = "✅ Publish selected activities"
    
    def unpublish_activities(self, request, queryset):
        """Bulk unpublish activities"""
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} activities unpublished.')
    unpublish_activities.short_description = "❌ Unpublish selected activities"
    
    def duplicate_activities(self, request, queryset):
        """Duplicate selected activities"""
        for activity in queryset:
            # Create a copy
            activity.pk = None
            activity.id = None
            activity.title = f"{activity.title} (Copy)"
            activity.slug = f"{activity.slug}-copy"
            activity.is_published = False
            activity.save()
        self.message_user(request, f'{queryset.count()} activities duplicated.')
    duplicate_activities.short_description = "📋 Duplicate selected activities"
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('video_asset').prefetch_related(
            'teacher_resources', 'student_resources'
        )


# ============================================================================
# COMMUNITY FORUM MANAGEMENT
# ============================================================================

@admin.register(ForumCategory)
class ForumCategoryAdmin(admin.ModelAdmin):
    """Admin configuration for ForumCategory model"""
    
    list_display = ['name', 'slug', 'icon', 'color', 'order', 'is_active', 'post_count']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Category Info', {
            'fields': ('id', 'name', 'slug', 'description')
        }),
        ('Display', {
            'fields': ('icon', 'color', 'order')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def post_count(self, obj):
        """Display number of posts in this category"""
        count = obj.forumpost_set.count()
        return format_html('<strong>{}</strong>', count)
    post_count.short_description = 'Posts'


class ForumCommentInline(admin.TabularInline):
    """Inline admin for forum comments"""
    model = ForumComment
    extra = 0
    readonly_fields = ['id', 'author', 'created_at']
    fields = ['author', 'content', 'is_deleted', 'created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')


@admin.register(ForumPost)
class ForumPostAdmin(admin.ModelAdmin):
    """
    Admin configuration for ForumPost model
    Includes moderation tools as specified in TRD
    """
    
    list_display = [
        'title', 'author', 'category', 'view_count', 'comment_count',
        'is_pinned', 'is_locked', 'created_at'
    ]
    list_filter = ['category', 'is_pinned', 'is_locked', 'created_at']
    search_fields = ['title', 'content', 'author__username', 'author__email']
    readonly_fields = ['id', 'view_count', 'created_at', 'updated_at', 'last_activity_at']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ForumCommentInline]
    
    # Moderation actions
    actions = ['pin_posts', 'unpin_posts', 'lock_posts', 'unlock_posts', 'delete_posts']
    
    fieldsets = (
        ('Post Content', {
            'fields': ('id', 'title', 'slug', 'content')
        }),
        ('Author & Category', {
            'fields': ('author', 'category', 'related_activity')
        }),
        ('Moderation', {
            'fields': ('is_pinned', 'is_locked'),
            'description': 'Admin moderation controls'
        }),
        ('Statistics', {
            'fields': ('view_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_activity_at'),
            'classes': ('collapse',)
        }),
    )
    
    def comment_count(self, obj):
        """Display number of comments"""
        count = obj.comments.filter(is_deleted=False).count()
        return format_html('<strong>{}</strong>', count)
    comment_count.short_description = 'Comments'
    
    def pin_posts(self, request, queryset):
        """Pin selected posts"""
        updated = queryset.update(is_pinned=True)
        self.message_user(request, f'{updated} posts pinned.')
    pin_posts.short_description = "📌 Pin selected posts"
    
    def unpin_posts(self, request, queryset):
        """Unpin selected posts"""
        updated = queryset.update(is_pinned=False)
        self.message_user(request, f'{updated} posts unpinned.')
    unpin_posts.short_description = "📌 Unpin selected posts"
    
    def lock_posts(self, request, queryset):
        """Lock selected posts (prevent new comments)"""
        updated = queryset.update(is_locked=True)
        self.message_user(request, f'{updated} posts locked.')
    lock_posts.short_description = "🔒 Lock selected posts"
    
    def unlock_posts(self, request, queryset):
        """Unlock selected posts"""
        updated = queryset.update(is_locked=False)
        self.message_user(request, f'{updated} posts unlocked.')
    unlock_posts.short_description = "🔓 Unlock selected posts"
    
    def delete_posts(self, request, queryset):
        """Delete selected posts (admin moderation)"""
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f'{count} posts deleted.')
    delete_posts.short_description = "🗑️ Delete selected posts"
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related(
            'author', 'category', 'related_activity'
        ).prefetch_related('comments')


@admin.register(ForumComment)
class ForumCommentAdmin(admin.ModelAdmin):
    """Admin configuration for ForumComment model"""
    
    list_display = ['post', 'author', 'content_preview', 'is_deleted', 'created_at']
    list_filter = ['is_deleted', 'created_at']
    search_fields = ['content', 'author__username', 'post__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    # Moderation actions
    actions = ['soft_delete_comments', 'restore_comments']
    
    fieldsets = (
        ('Comment', {
            'fields': ('id', 'post', 'author', 'parent_comment', 'content')
        }),
        ('Moderation', {
            'fields': ('is_deleted',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def content_preview(self, obj):
        """Show preview of comment content"""
        if len(obj.content) > 50:
            return f"{obj.content[:50]}..."
        return obj.content
    content_preview.short_description = 'Content'
    
    def soft_delete_comments(self, request, queryset):
        """Soft delete comments (mark as deleted)"""
        updated = queryset.update(is_deleted=True)
        self.message_user(request, f'{updated} comments marked as deleted.')
    soft_delete_comments.short_description = "🗑️ Soft delete comments"
    
    def restore_comments(self, request, queryset):
        """Restore soft-deleted comments"""
        updated = queryset.update(is_deleted=False)
        self.message_user(request, f'{updated} comments restored.')
    restore_comments.short_description = "♻️ Restore deleted comments"
    
    def get_queryset(self, request):
        """Optimize queryset"""
        return super().get_queryset(request).select_related('post', 'author', 'parent_comment')
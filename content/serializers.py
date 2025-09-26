from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    VideoAsset, Resource, Playlist, PlaylistItem, PlaylistShare, 
    AuditLog, AssetView, AssetDownload, DailyAssetStats
)

User = get_user_model()


class VideoAssetSerializer(serializers.ModelSerializer):
    """Serializer for VideoAsset model"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    grade_display = serializers.CharField(source='get_grade_display', read_only=True)
    topic_display = serializers.CharField(source='get_topic_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    file_size_formatted = serializers.CharField(read_only=True)
    
    class Meta:
        model = VideoAsset
        fields = [
            'id', 'title', 'description', 'grade', 'grade_display', 
            'topic', 'topic_display', 'tags', 'duration', 'duration_formatted',
            'file_size', 'file_size_formatted', 'storage_uri', 'thumbnail_uri',
            'owner', 'owner_name', 'school', 'school_name', 'status', 'status_display',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner', 'school', 'created_at', 'updated_at',
            'owner_name', 'school_name', 'grade_display', 'topic_display',
            'status_display', 'duration_formatted', 'file_size_formatted'
        ]


class VideoAssetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating VideoAsset from upload metadata"""
    
    class Meta:
        model = VideoAsset
        fields = [
            'title', 'description', 'grade', 'topic', 'tags',
            'duration', 'file_size', 'storage_uri', 'thumbnail_uri'
        ]
    
    def create(self, validated_data):
        """Create video asset with owner and school from request"""
        request = self.context['request']
        validated_data['owner'] = request.user
        validated_data['school'] = request.user.school
        return super().create(validated_data)


class ResourceSerializer(serializers.ModelSerializer):
    """Serializer for Resource model"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    grade_display = serializers.CharField(source='get_grade_display', read_only=True)
    topic_display = serializers.CharField(source='get_topic_display', read_only=True)
    file_type_display = serializers.CharField(source='get_file_type_display', read_only=True)
    file_size_formatted = serializers.CharField(read_only=True)
    
    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'description', 'file_uri', 'file_type', 'file_type_display',
            'file_size', 'file_size_formatted', 'grade', 'grade_display',
            'topic', 'topic_display', 'tags', 'owner', 'owner_name',
            'school', 'school_name', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner', 'school', 'created_at', 'updated_at',
            'owner_name', 'school_name', 'grade_display', 'topic_display',
            'file_type_display', 'file_size_formatted'
        ]


class ResourceCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Resource from upload metadata"""
    
    class Meta:
        model = Resource
        fields = [
            'title', 'description', 'file_uri', 'file_type', 'file_size',
            'grade', 'topic', 'tags'
        ]
    
    def create(self, validated_data):
        """Create resource with owner and school from request"""
        request = self.context['request']
        validated_data['owner'] = request.user
        validated_data['school'] = request.user.school
        return super().create(validated_data)


class PlaylistItemSerializer(serializers.ModelSerializer):
    """Serializer for PlaylistItem model"""
    
    video_title = serializers.CharField(source='video_asset.title', read_only=True)
    video_duration = serializers.CharField(source='video_asset.duration_formatted', read_only=True)
    
    class Meta:
        model = PlaylistItem
        fields = [
            'id', 'video_asset', 'video_title', 'video_duration',
            'order', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'video_title', 'video_duration']


class PlaylistSerializer(serializers.ModelSerializer):
    """Serializer for Playlist model"""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    school_name = serializers.CharField(source='school.name', read_only=True)
    video_count = serializers.IntegerField(read_only=True)
    total_duration_formatted = serializers.CharField(read_only=True)
    items = PlaylistItemSerializer(source='playlistitem_set', many=True, read_only=True)
    
    class Meta:
        model = Playlist
        fields = [
            'id', 'name', 'description', 'owner', 'owner_name',
            'school', 'school_name', 'is_public', 'video_count',
            'total_duration_formatted', 'items', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner', 'school', 'created_at', 'updated_at',
            'owner_name', 'school_name', 'video_count', 
            'total_duration_formatted', 'items'
        ]
    
    def create(self, validated_data):
        """Create playlist with owner and school from request"""
        request = self.context['request']
        validated_data['owner'] = request.user
        validated_data['school'] = request.user.school
        return super().create(validated_data)


class SignedUploadRequestSerializer(serializers.Serializer):
    """Serializer for signed upload URL request"""
    
    CATEGORY_CHOICES = [
        ('video', 'Video'),
        ('resource', 'Resource'),
    ]
    
    filename = serializers.CharField(max_length=255)
    file_size = serializers.IntegerField(min_value=1)
    content_type = serializers.CharField(max_length=100)
    category = serializers.ChoiceField(choices=CATEGORY_CHOICES)
    
    # Optional metadata for immediate asset creation
    title = serializers.CharField(max_length=200, required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    grade = serializers.CharField(max_length=2, required=False, allow_blank=True)
    topic = serializers.CharField(max_length=50, required=False, allow_blank=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True
    )


class SignedUploadResponseSerializer(serializers.Serializer):
    """Serializer for signed upload URL response"""
    
    upload_url = serializers.URLField()
    public_url = serializers.URLField()
    storage_path = serializers.CharField()
    filename = serializers.CharField()
    expires_at = serializers.DateTimeField()
    metadata = serializers.DictField()


class UploadCompleteSerializer(serializers.Serializer):
    """Serializer for upload completion notification"""
    
    storage_path = serializers.CharField()
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True)
    grade = serializers.CharField(max_length=2, required=False, allow_blank=True)
    topic = serializers.CharField(max_length=50, required=False, allow_blank=True)
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        allow_empty=True
    )
    duration = serializers.IntegerField(required=False, allow_null=True)
    
    def validate_storage_path(self, value):
        """Validate that storage path exists and belongs to user"""
        # This would typically check Firebase Storage
        # For now, we'll do basic validation
        if not value or len(value) < 10:
            raise serializers.ValidationError("Invalid storage path")
        return value


class PlaylistShareSerializer(serializers.ModelSerializer):
    """Serializer for PlaylistShare model"""
    
    playlist_name = serializers.CharField(source='playlist.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_valid = serializers.BooleanField(read_only=True)
    share_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PlaylistShare
        fields = [
            'id', 'share_token', 'playlist', 'playlist_name',
            'created_by', 'created_by_name', 'expires_at', 'is_active',
            'is_expired', 'is_valid', 'view_count', 'last_accessed',
            'share_url', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'share_token', 'created_by', 'view_count', 'last_accessed',
            'created_at', 'updated_at', 'playlist_name', 'created_by_name',
            'is_expired', 'is_valid', 'share_url'
        ]
    
    def get_share_url(self, obj):
        """Generate full share URL"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/api/shared/{obj.share_token}/')
        return f'/api/shared/{obj.share_token}/'


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for AuditLog model"""
    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'action', 'action_display', 'user', 'user_name',
            'metadata', 'ip_address', 'created_at'
        ]
        read_only_fields = ['id', 'created_at', 'user_name', 'action_display']


class AssetViewSerializer(serializers.ModelSerializer):
    """Serializer for AssetView model"""
    
    asset_title = serializers.CharField(source='asset.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = AssetView
        fields = [
            'id', 'asset', 'asset_title', 'user', 'user_name',
            'session_id', 'duration_watched', 'completion_percentage',
            'referrer', 'viewed_at'
        ]
        read_only_fields = ['id', 'viewed_at', 'asset_title', 'user_name']


class AssetDownloadSerializer(serializers.ModelSerializer):
    """Serializer for AssetDownload model"""
    
    resource_title = serializers.CharField(source='resource.title', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = AssetDownload
        fields = [
            'id', 'resource', 'resource_title', 'user', 'user_name',
            'file_size', 'download_completed', 'ip_address', 'downloaded_at'
        ]
        read_only_fields = ['id', 'downloaded_at', 'resource_title', 'user_name']


class DailyAssetStatsSerializer(serializers.ModelSerializer):
    """Serializer for DailyAssetStats model"""
    
    asset_title = serializers.CharField(source='asset.title', read_only=True)
    
    class Meta:
        model = DailyAssetStats
        fields = [
            'asset', 'asset_title', 'date', 'view_count', 'unique_viewers',
            'total_watch_time', 'avg_completion_rate', 'playlist_adds',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'asset_title']


class AnalyticsViewRequestSerializer(serializers.Serializer):
    """Serializer for analytics view tracking request"""
    
    video_id = serializers.UUIDField(required=True)
    session_id = serializers.CharField(max_length=50, required=False)
    duration_watched = serializers.IntegerField(min_value=0, required=False)
    completion_percentage = serializers.FloatField(min_value=0.0, max_value=1.0, required=False)
    referrer = serializers.URLField(required=False, allow_blank=True)

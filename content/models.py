from django.db import models
from django.contrib.auth import get_user_model
from accounts.models import School
import uuid

User = get_user_model()

# Canonical Taxonomy Constants
GRADE_CHOICES = [
    ('K', 'Kindergarten'),
    ('1', 'Grade 1'),
    ('2', 'Grade 2'),
    ('3', 'Grade 3'),
    ('4', 'Grade 4'),
    ('5', 'Grade 5'),
    ('6', 'Grade 6'),
    ('7', 'Grade 7'),
    ('8', 'Grade 8'),
]

TOPIC_CHOICES = [
    ('fractions_basics', 'Fractions Basics'),
    ('equivalent_fractions', 'Equivalent Fractions'),
    ('comparing_ordering', 'Comparing/Ordering'),
    ('number_line', 'Number Line'),
    ('mixed_improper', 'Mixed ↔ Improper'),
    ('add_subtract_fractions', 'Add/Subtract Fractions'),
    ('multiply_divide_fractions', 'Multiply/Divide Fractions (6+)'),
    ('decimals_percents', 'Decimals & Percents'),
    ('ratio_proportion', 'Ratio/Proportion (6+)'),
    ('word_problems', 'Word Problems'),
]

STATUS_CHOICES = [
    ('DRAFT', 'Draft'),
    ('PENDING', 'Pending Review'),
    ('PUBLISHED', 'Published'),
    ('REJECTED', 'Rejected'),
]


class VideoAsset(models.Model):
    """Video content asset with metadata and Firebase Storage integration"""
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, help_text="Detailed description of the video content")
    
    # Taxonomy
    grade = models.CharField(
        max_length=2, 
        choices=GRADE_CHOICES,
        help_text="Target grade level for this content"
    )
    topic = models.CharField(
        max_length=50, 
        choices=TOPIC_CHOICES,
        help_text="Primary topic covered in this video"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional tags for categorization (JSON array)"
    )
    
    # Video Metadata
    duration = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Video duration in seconds"
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    
    # Firebase Storage
    storage_uri = models.URLField(
        help_text="Firebase Storage path for the video file"
    )
    thumbnail_uri = models.URLField(
        blank=True,
        help_text="Firebase Storage path for video thumbnail"
    )
    
    # Organization & Ownership
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        help_text="User who uploaded this video"
    )
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE,
        help_text="School this video belongs to"
    )
    
    # Status & Workflow
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='DRAFT',
        help_text="Current status in the approval workflow"
    )
    submitted_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this video was submitted for review"
    )
    reviewed_by = models.ForeignKey(
        User, 
        null=True, 
        blank=True,
        on_delete=models.SET_NULL, 
        related_name='reviewed_videos',
        help_text="Admin who reviewed this video"
    )
    reviewed_at = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When this video was reviewed"
    )
    review_notes = models.TextField(
        blank=True,
        help_text="Notes from the reviewer"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Video Asset'
        verbose_name_plural = 'Video Assets'
        indexes = [
            models.Index(fields=['school', 'status']),
            models.Index(fields=['grade', 'topic']),
            models.Index(fields=['owner', 'created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_grade_display()} - {self.get_topic_display()})"
    
    @property
    def is_published(self):
        """Check if video is published and visible to others"""
        return self.status == 'PUBLISHED'
    
    @property
    def duration_formatted(self):
        """Return formatted duration (MM:SS)"""
        if not self.duration:
            return "Unknown"
        
        minutes = self.duration // 60
        seconds = self.duration % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def file_size_formatted(self):
        """Return formatted file size"""
        if not self.file_size:
            return "Unknown"
        
        # Convert bytes to MB
        size_mb = self.file_size / (1024 * 1024)
        if size_mb < 1:
            return f"{self.file_size / 1024:.1f} KB"
        elif size_mb < 1024:
            return f"{size_mb:.1f} MB"
        else:
            return f"{size_mb / 1024:.1f} GB"


class Resource(models.Model):
    """Non-video resources like PDFs, documents, etc."""
    
    RESOURCE_TYPE_CHOICES = [
        ('pdf', 'PDF Document'),
        ('doc', 'Word Document'),
        ('docx', 'Word Document (DOCX)'),
        ('ppt', 'PowerPoint'),
        ('pptx', 'PowerPoint (PPTX)'),
        ('xls', 'Excel Spreadsheet'),
        ('xlsx', 'Excel Spreadsheet (XLSX)'),
        ('txt', 'Text File'),
        ('image', 'Image File'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # File Information
    file_uri = models.URLField(help_text="Firebase Storage path for the resource file")
    file_type = models.CharField(
        max_length=10, 
        choices=RESOURCE_TYPE_CHOICES,
        help_text="Type of resource file"
    )
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        help_text="File size in bytes"
    )
    
    # Taxonomy (optional for resources)
    grade = models.CharField(
        max_length=2, 
        choices=GRADE_CHOICES,
        blank=True,
        help_text="Target grade level (optional)"
    )
    topic = models.CharField(
        max_length=50, 
        choices=TOPIC_CHOICES,
        blank=True,
        help_text="Related topic (optional)"
    )
    tags = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional tags for categorization"
    )
    
    # Organization & Ownership
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    
    # Status
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='DRAFT'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Resource'
        verbose_name_plural = 'Resources'
        indexes = [
            models.Index(fields=['school', 'status']),
            models.Index(fields=['file_type', 'status']),
            models.Index(fields=['owner', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_file_type_display()})"
    
    @property
    def file_size_formatted(self):
        """Return formatted file size"""
        if not self.file_size:
            return "Unknown"
        
        # Convert bytes to appropriate unit
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"


class Playlist(models.Model):
    """Collection of videos organized by teachers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Organization & Ownership
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE)
    
    # Metadata
    is_public = models.BooleanField(
        default=False,
        help_text="Whether this playlist is visible to other teachers in the school"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Playlist'
        verbose_name_plural = 'Playlists'
        indexes = [
            models.Index(fields=['school', 'is_public']),
            models.Index(fields=['owner', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} (by {self.owner.get_full_name()})"
    
    @property
    def video_count(self):
        """Get count of videos in this playlist"""
        return self.playlistitem_set.count()
    
    @property
    def total_duration(self):
        """Get total duration of all videos in playlist (seconds)"""
        total = 0
        for item in self.playlistitem_set.select_related('video_asset'):
            if item.video_asset.duration:
                total += item.video_asset.duration
        return total
    
    @property
    def total_duration_formatted(self):
        """Return formatted total duration"""
        if not self.total_duration:
            return "0:00"
        
        hours = self.total_duration // 3600
        minutes = (self.total_duration % 3600) // 60
        seconds = self.total_duration % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"


class PlaylistItem(models.Model):
    """Individual video within a playlist with ordering"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    playlist = models.ForeignKey(Playlist, on_delete=models.CASCADE)
    video_asset = models.ForeignKey(VideoAsset, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(help_text="Position in the playlist (1-based)")
    
    # Optional item-specific metadata
    notes = models.TextField(
        blank=True,
        help_text="Teacher's notes about this video in the context of the playlist"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['playlist', 'order']
        unique_together = ['playlist', 'order']
        verbose_name = 'Playlist Item'
        verbose_name_plural = 'Playlist Items'
        indexes = [
            models.Index(fields=['playlist', 'order']),
        ]
    
    def __str__(self):
        return f"{self.playlist.name} - {self.order}: {self.video_asset.title}"
    
    def save(self, *args, **kwargs):
        """Auto-assign order if not provided"""
        if not self.order:
            last_item = PlaylistItem.objects.filter(playlist=self.playlist).order_by('-order').first()
            self.order = (last_item.order + 1) if last_item else 1
        super().save(*args, **kwargs)
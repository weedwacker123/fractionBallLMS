"""
File validation utilities for Firebase Storage uploads
Provides security checks and file type validation
"""

import os
import logging
from typing import Tuple, Optional

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    logging.warning("python-magic not available. File content validation will be skipped.")

logger = logging.getLogger(__name__)


class FileValidator:
    """
    Validates file uploads for security and compliance
    """
    
    # Maximum file sizes (in bytes)
    MAX_FILE_SIZES = {
        'video': 500 * 1024 * 1024,      # 500 MB
        'resource': 50 * 1024 * 1024,    # 50 MB
        'thumbnail': 10 * 1024 * 1024,   # 10 MB
        'lesson': 10 * 1024 * 1024,      # 10 MB
    }
    
    # Allowed MIME types for each file type
    ALLOWED_MIME_TYPES = {
        'video': [
            'video/mp4',
            'video/quicktime',
            'video/x-msvideo',
            'video/x-matroska',
            'video/webm',
        ],
        'resource': [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain',
            'image/jpeg',
            'image/png',
            'image/gif',
            'image/webp',
        ],
        'thumbnail': [
            'image/jpeg',
            'image/png',
            'image/webp',
            'image/gif',
        ],
        'lesson': [
            'application/pdf',
        ]
    }
    
    # Dangerous file extensions (always reject)
    DANGEROUS_EXTENSIONS = [
        '.exe', '.bat', '.cmd', '.com', '.pif', '.scr',
        '.vbs', '.js', '.jar', '.msi', '.app', '.deb',
        '.rpm', '.sh', '.bash', '.ps1', '.psm1',
    ]
    
    @staticmethod
    def validate_file_type(file_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that the file type is supported
        
        Args:
            file_type: Type of file ('video', 'resource', 'thumbnail', 'lesson')
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        valid_types = ['video', 'resource', 'thumbnail', 'lesson']
        
        if file_type not in valid_types:
            return False, f"Invalid file type. Must be one of: {', '.join(valid_types)}"
        
        return True, None
    
    @staticmethod
    def validate_file_size(file_size: int, file_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that the file size is within limits
        
        Args:
            file_size: Size of file in bytes
            file_type: Type of file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if file_size <= 0:
            return False, "File size must be greater than 0"
        
        max_size = FileValidator.MAX_FILE_SIZES.get(file_type)
        if not max_size:
            return False, f"Unknown file type: {file_type}"
        
        if file_size > max_size:
            max_size_mb = max_size / (1024 * 1024)
            file_size_mb = file_size / (1024 * 1024)
            return False, (
                f"File size ({file_size_mb:.1f} MB) exceeds maximum "
                f"allowed size ({max_size_mb:.0f} MB) for {file_type}"
            )
        
        return True, None
    
    @staticmethod
    def validate_mime_type(content_type: str, file_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that the MIME type is allowed for this file type
        
        Args:
            content_type: MIME type of the file
            file_type: Type of file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        allowed_types = FileValidator.ALLOWED_MIME_TYPES.get(file_type, [])
        
        if content_type not in allowed_types:
            return False, (
                f"Content type '{content_type}' is not allowed for {file_type}. "
                f"Allowed types: {', '.join(allowed_types)}"
            )
        
        return True, None
    
    @staticmethod
    def validate_file_name(file_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate file name for security issues
        
        Args:
            file_name: Name of the file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not file_name:
            return False, "File name is required"
        
        # Check for path traversal attempts
        if '..' in file_name or '/' in file_name or '\\' in file_name:
            return False, "File name contains invalid characters"
        
        # Check file extension
        _, ext = os.path.splitext(file_name.lower())
        
        # Check for dangerous extensions
        if ext in FileValidator.DANGEROUS_EXTENSIONS:
            return False, f"File extension '{ext}' is not allowed for security reasons"
        
        # Check file name length
        if len(file_name) > 255:
            return False, "File name is too long (max 255 characters)"
        
        return True, None
    
    @staticmethod
    def validate_upload_request(
        file_type: str,
        content_type: str,
        file_size: int,
        file_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate all aspects of an upload request
        
        Args:
            file_type: Type of file
            content_type: MIME type
            file_size: Size in bytes
            file_name: Name of file
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate file type
        is_valid, error = FileValidator.validate_file_type(file_type)
        if not is_valid:
            return False, error
        
        # Validate file size
        is_valid, error = FileValidator.validate_file_size(file_size, file_type)
        if not is_valid:
            return False, error
        
        # Validate MIME type
        is_valid, error = FileValidator.validate_mime_type(content_type, file_type)
        if not is_valid:
            return False, error
        
        # Validate file name
        is_valid, error = FileValidator.validate_file_name(file_name)
        if not is_valid:
            return False, error
        
        logger.info(
            f"Upload request validated: {file_type}, {content_type}, "
            f"{file_size} bytes, {file_name}"
        )
        
        return True, None
    
    @staticmethod
    def validate_file_content(file_path: str, expected_mime_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate actual file content matches expected MIME type
        Uses python-magic to check file signature
        
        Args:
            file_path: Path to the file on disk
            expected_mime_type: Expected MIME type
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not HAS_MAGIC:
            logger.warning("python-magic not available, skipping file content validation")
            return True, None
        
        try:
            # Get actual MIME type from file content
            mime = magic.Magic(mime=True)
            actual_mime_type = mime.from_file(file_path)
            
            # Check if it matches expected
            if not actual_mime_type.startswith(expected_mime_type.split('/')[0]):
                return False, (
                    f"File content does not match declared type. "
                    f"Expected: {expected_mime_type}, "
                    f"Actual: {actual_mime_type}"
                )
            
            logger.info(f"File content validated: {actual_mime_type}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error validating file content: {e}")
            return False, f"Failed to validate file content: {str(e)}"


class UploadRateLimiter:
    """
    Rate limiter for file uploads to prevent abuse
    """
    
    # Maximum uploads per user per time period
    MAX_UPLOADS_PER_HOUR = 50
    MAX_UPLOADS_PER_DAY = 200
    
    # Maximum total storage per user (bytes)
    MAX_USER_STORAGE = 10 * 1024 * 1024 * 1024  # 10 GB
    
    @staticmethod
    def check_upload_limit(user_id: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user has exceeded upload limits
        
        Args:
            user_id: ID of the user
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        from django.core.cache import cache
        from datetime import datetime, timedelta
        
        # Check hourly limit
        hour_key = f"upload_count_hour_{user_id}_{datetime.now().strftime('%Y%m%d%H')}"
        hour_count = cache.get(hour_key, 0)
        
        if hour_count >= UploadRateLimiter.MAX_UPLOADS_PER_HOUR:
            return False, (
                f"Upload limit exceeded. Maximum {UploadRateLimiter.MAX_UPLOADS_PER_HOUR} "
                "uploads per hour allowed."
            )
        
        # Check daily limit
        day_key = f"upload_count_day_{user_id}_{datetime.now().strftime('%Y%m%d')}"
        day_count = cache.get(day_key, 0)
        
        if day_count >= UploadRateLimiter.MAX_UPLOADS_PER_DAY:
            return False, (
                f"Upload limit exceeded. Maximum {UploadRateLimiter.MAX_UPLOADS_PER_DAY} "
                "uploads per day allowed."
            )
        
        # Increment counters
        cache.set(hour_key, hour_count + 1, 3600)  # 1 hour TTL
        cache.set(day_key, day_count + 1, 86400)   # 24 hour TTL
        
        return True, None
    
    @staticmethod
    def check_storage_quota(user_id: int, new_file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Check if user has enough storage quota
        
        Args:
            user_id: ID of the user
            new_file_size: Size of new file in bytes
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        from content.models import VideoAsset, Resource
        from django.db.models import Sum
        
        # Calculate current storage usage
        video_size = VideoAsset.objects.filter(owner_id=user_id).aggregate(
            total=Sum('file_size')
        )['total'] or 0
        
        resource_size = Resource.objects.filter(owner_id=user_id).aggregate(
            total=Sum('file_size')
        )['total'] or 0
        
        current_usage = video_size + resource_size
        new_total = current_usage + new_file_size
        
        if new_total > UploadRateLimiter.MAX_USER_STORAGE:
            max_gb = UploadRateLimiter.MAX_USER_STORAGE / (1024 * 1024 * 1024)
            current_gb = current_usage / (1024 * 1024 * 1024)
            return False, (
                f"Storage quota exceeded. You are using {current_gb:.2f} GB "
                f"of your {max_gb:.0f} GB limit."
            )
        
        return True, None


def validate_and_check_limits(
    user_id: int,
    file_type: str,
    content_type: str,
    file_size: int,
    file_name: str
) -> Tuple[bool, Optional[str]]:
    """
    Comprehensive validation and rate limiting check
    
    Args:
        user_id: ID of the user
        file_type: Type of file
        content_type: MIME type
        file_size: Size in bytes
        file_name: Name of file
    
    Returns:
        Tuple of (is_allowed, error_message)
    """
    # Validate file
    is_valid, error = FileValidator.validate_upload_request(
        file_type, content_type, file_size, file_name
    )
    if not is_valid:
        return False, error
    
    # Check rate limits
    is_allowed, error = UploadRateLimiter.check_upload_limit(user_id)
    if not is_allowed:
        return False, error
    
    # Check storage quota
    is_allowed, error = UploadRateLimiter.check_storage_quota(user_id, file_size)
    if not is_allowed:
        return False, error
    
    return True, None







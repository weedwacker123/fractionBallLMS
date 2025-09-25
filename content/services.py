"""
Firebase Storage services for handling file uploads and CDN delivery
"""
import firebase_admin
from firebase_admin import storage
from django.conf import settings
from django.core.exceptions import ValidationError
import uuid
import mimetypes
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class FirebaseStorageService:
    """Service for handling Firebase Storage operations"""
    
    # File size limits (in bytes)
    MAX_VIDEO_SIZE = 500 * 1024 * 1024  # 500MB
    MAX_RESOURCE_SIZE = 50 * 1024 * 1024  # 50MB
    
    # Allowed file types
    ALLOWED_VIDEO_TYPES = [
        'video/mp4', 'video/mpeg', 'video/quicktime', 
        'video/x-msvideo', 'video/webm'
    ]
    
    ALLOWED_RESOURCE_TYPES = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        'image/jpeg', 'image/png', 'image/gif'
    ]
    
    def __init__(self):
        """Initialize Firebase Storage client"""
        try:
            self.bucket = storage.bucket()
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Storage: {e}")
            self.bucket = None
    
    def validate_file(self, filename, file_size, content_type, file_category='video'):
        """
        Validate file before upload
        
        Args:
            filename: Name of the file
            file_size: Size of file in bytes
            content_type: MIME type of the file
            file_category: 'video' or 'resource'
            
        Raises:
            ValidationError: If file doesn't meet requirements
        """
        # Check file size
        max_size = self.MAX_VIDEO_SIZE if file_category == 'video' else self.MAX_RESOURCE_SIZE
        if file_size > max_size:
            raise ValidationError(
                f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds maximum "
                f"allowed size ({max_size / 1024 / 1024}MB)"
            )
        
        # Check content type
        allowed_types = self.ALLOWED_VIDEO_TYPES if file_category == 'video' else self.ALLOWED_RESOURCE_TYPES
        if content_type not in allowed_types:
            raise ValidationError(f"File type '{content_type}' is not allowed")
        
        # Check filename
        if not filename or len(filename) > 255:
            raise ValidationError("Invalid filename")
        
        return True
    
    def generate_upload_url(self, filename, file_size, content_type, 
                          file_category='video', user_id=None, school_id=None):
        """
        Generate a signed URL for direct upload to Firebase Storage
        
        Args:
            filename: Original filename
            file_size: File size in bytes
            content_type: MIME type
            file_category: 'video' or 'resource'
            user_id: ID of the uploading user
            school_id: ID of the user's school
            
        Returns:
            dict: Upload URL and metadata
        """
        if not self.bucket:
            raise Exception("Firebase Storage not initialized")
        
        # Validate file
        self.validate_file(filename, file_size, content_type, file_category)
        
        # Generate unique filename
        file_extension = filename.split('.')[-1].lower()
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        
        # Create storage path
        timestamp = datetime.now().strftime('%Y/%m/%d')
        storage_path = f"{file_category}s/{timestamp}/{unique_filename}"
        
        # Get blob reference
        blob = self.bucket.blob(storage_path)
        
        # Set metadata
        metadata = {
            'originalFilename': filename,
            'uploadedBy': str(user_id) if user_id else 'unknown',
            'schoolId': str(school_id) if school_id else 'unknown',
            'category': file_category,
            'uploadTimestamp': datetime.utcnow().isoformat()
        }
        blob.metadata = metadata
        
        # Generate signed upload URL (valid for 1 hour)
        upload_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="PUT",
            content_type=content_type
        )
        
        # Generate public download URL (for streaming)
        public_url = f"https://firebasestorage.googleapis.com/v0/b/{self.bucket.name}/o/{storage_path.replace('/', '%2F')}?alt=media"
        
        return {
            'upload_url': upload_url,
            'public_url': public_url,
            'storage_path': storage_path,
            'filename': unique_filename,
            'expires_at': (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            'metadata': metadata
        }
    
    def generate_download_url(self, storage_path, expires_in_hours=24):
        """
        Generate a signed download URL for resources (not videos)
        Videos should use public streaming URLs only
        
        Args:
            storage_path: Path to file in Firebase Storage
            expires_in_hours: URL expiration time in hours
            
        Returns:
            str: Signed download URL
        """
        if not self.bucket:
            raise Exception("Firebase Storage not initialized")
        
        # Only allow download URLs for resources, not videos
        if storage_path.startswith('videos/'):
            raise ValidationError("Download URLs not allowed for videos - use streaming only")
        
        blob = self.bucket.blob(storage_path)
        
        # Generate signed download URL
        download_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=expires_in_hours),
            method="GET"
        )
        
        return download_url
    
    def get_file_metadata(self, storage_path):
        """
        Get metadata for a file in Firebase Storage
        
        Args:
            storage_path: Path to file in Firebase Storage
            
        Returns:
            dict: File metadata
        """
        if not self.bucket:
            raise Exception("Firebase Storage not initialized")
        
        blob = self.bucket.blob(storage_path)
        
        try:
            blob.reload()
            return {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created,
                'updated': blob.updated,
                'metadata': blob.metadata or {}
            }
        except Exception as e:
            logger.error(f"Failed to get metadata for {storage_path}: {e}")
            return None
    
    def delete_file(self, storage_path):
        """
        Delete a file from Firebase Storage
        
        Args:
            storage_path: Path to file in Firebase Storage
            
        Returns:
            bool: True if successful
        """
        if not self.bucket:
            raise Exception("Firebase Storage not initialized")
        
        try:
            blob = self.bucket.blob(storage_path)
            blob.delete()
            logger.info(f"Deleted file: {storage_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {storage_path}: {e}")
            return False
    
    def get_public_url(self, storage_path):
        """
        Get public URL for streaming (videos) or direct access
        
        Args:
            storage_path: Path to file in Firebase Storage
            
        Returns:
            str: Public URL
        """
        return f"https://firebasestorage.googleapis.com/v0/b/{self.bucket.name}/o/{storage_path.replace('/', '%2F')}?alt=media"


# Global instance
firebase_storage = FirebaseStorageService()

"""
Local file storage for development/testing
Use this when Firebase is not configured
"""
import os
import uuid
import logging
from pathlib import Path
from django.conf import settings
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)


class LocalStorageService:
    """
    Local file storage service for development
    Mimics Firebase Storage API but stores files locally
    """
    
    def __init__(self):
        """Initialize local storage"""
        self.media_root = Path(settings.BASE_DIR) / 'media'
        self.media_root.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.media_root / 'videos').mkdir(exist_ok=True)
        (self.media_root / 'resources').mkdir(exist_ok=True)
        (self.media_root / 'thumbnails').mkdir(exist_ok=True)
        (self.media_root / 'lesson-plans').mkdir(exist_ok=True)
        
        self.storage = FileSystemStorage(location=str(self.media_root))
        logger.info(f"📁 Local storage initialized at: {self.media_root}")
    
    def save_file(self, uploaded_file, file_type='video'):
        """
        Save an uploaded file locally
        
        Args:
            uploaded_file: Django UploadedFile object
            file_type: Type of file ('video', 'resource', etc.)
        
        Returns:
            file_path: Relative path to the saved file
        """
        # Generate unique filename
        ext = Path(uploaded_file.name).suffix
        unique_id = uuid.uuid4().hex[:12]
        filename = f"{unique_id}{ext}"
        
        # Determine subdirectory
        type_map = {
            'video': 'videos',
            'resource': 'resources',
            'thumbnail': 'thumbnails',
            'lesson': 'lesson-plans'
        }
        subdir = type_map.get(file_type, 'uploads')
        
        # Full path
        file_path = f"{subdir}/{filename}"
        
        # Save file
        saved_path = self.storage.save(file_path, uploaded_file)
        
        logger.info(f"✅ File saved locally: {saved_path}")
        return saved_path
    
    def get_file_url(self, file_path):
        """
        Get URL for accessing a file
        
        Args:
            file_path: Path to the file
        
        Returns:
            URL string
        """
        return f"/media/{file_path}"
    
    def delete_file(self, file_path):
        """
        Delete a file
        
        Args:
            file_path: Path to the file
        
        Returns:
            True if successful
        """
        try:
            if self.storage.exists(file_path):
                self.storage.delete(file_path)
                logger.info(f"🗑️  File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False
    
    def file_exists(self, file_path):
        """Check if file exists"""
        return self.storage.exists(file_path)
    
    def get_file_size(self, file_path):
        """Get file size in bytes"""
        try:
            return self.storage.size(file_path)
        except:
            return 0


# Singleton instance
_local_storage = None


def get_local_storage():
    """Get or create local storage instance"""
    global _local_storage
    if _local_storage is None:
        _local_storage = LocalStorageService()
    return _local_storage








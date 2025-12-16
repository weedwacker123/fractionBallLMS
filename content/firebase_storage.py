"""
Firebase Storage service for handling file uploads and downloads
Provides secure upload URLs and streaming access for videos and resources
"""

import os
import uuid
import logging
import mimetypes
from datetime import timedelta
from typing import Optional, Tuple

from django.conf import settings
from google.cloud import storage
from google.oauth2 import service_account
import firebase_admin
from firebase_admin import credentials

logger = logging.getLogger(__name__)


class FirebaseStorageService:
    """
    Service for interacting with Firebase Storage
    Handles file uploads, signed URLs, and storage management
    """
    
    def __init__(self):
        """Initialize Firebase Storage client"""
        self.bucket_name = f"{settings.FIREBASE_CONFIG.get('project_id')}.appspot.com"
        self.storage_client = None
        self.bucket = None
        self._initialize_storage()
    
    def _initialize_storage(self):
        """Initialize Google Cloud Storage client with Firebase credentials"""
        try:
            # Create credentials from Firebase config
            creds_dict = settings.FIREBASE_CONFIG
            credentials_obj = service_account.Credentials.from_service_account_info(creds_dict)
            
            # Initialize storage client
            self.storage_client = storage.Client(
                credentials=credentials_obj,
                project=creds_dict.get('project_id')
            )
            
            # Get bucket
            self.bucket = self.storage_client.bucket(self.bucket_name)
            logger.info(f"✅ Firebase Storage initialized: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"❌ Firebase Storage initialization failed: {e}")
            raise
    
    def generate_upload_url(
        self,
        file_type: str,
        content_type: str,
        file_size: int,
        user_id: int
    ) -> Tuple[str, str]:
        """
        Generate a signed upload URL for client-side file uploads
        
        Args:
            file_type: Type of file ('video', 'resource', 'thumbnail', 'lesson')
            content_type: MIME type of the file
            file_size: Size of the file in bytes
            user_id: ID of the user uploading
        
        Returns:
            Tuple of (upload_url, file_path)
        """
        # Validate file type
        if file_type not in ['video', 'resource', 'thumbnail', 'lesson']:
            raise ValueError(f"Invalid file type: {file_type}")
        
        # Validate content type
        allowed_types = self._get_allowed_content_types(file_type)
        if content_type not in allowed_types:
            raise ValueError(f"Content type {content_type} not allowed for {file_type}")
        
        # Validate file size
        max_size = self._get_max_file_size(file_type)
        if file_size > max_size:
            raise ValueError(
                f"File size {file_size} exceeds maximum {max_size} for {file_type}"
            )
        
        # Generate unique file path
        file_path = self._generate_file_path(file_type, content_type, user_id)
        
        # Create blob
        blob = self.bucket.blob(file_path)
        
        # Generate signed upload URL (valid for 1 hour)
        upload_url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(hours=1),
            method="PUT",
            content_type=content_type,
            headers={"x-goog-meta-uploader": str(user_id)}
        )
        
        logger.info(f"Generated upload URL for {file_type}: {file_path}")
        return upload_url, file_path
    
    def generate_download_url(
        self,
        file_path: str,
        expiration_minutes: int = 60
    ) -> str:
        """
        Generate a signed download URL for accessing files
        
        Args:
            file_path: Path to file in storage
            expiration_minutes: How long the URL should be valid
        
        Returns:
            Signed download URL
        """
        try:
            blob = self.bucket.blob(file_path)
            
            # Generate signed URL
            download_url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expiration_minutes),
                method="GET"
            )
            
            return download_url
            
        except Exception as e:
            logger.error(f"Error generating download URL for {file_path}: {e}")
            raise
    
    def generate_streaming_url(
        self,
        file_path: str,
        expiration_minutes: int = 60
    ) -> str:
        """
        Generate a streaming URL for videos
        Same as download URL but with appropriate headers
        
        Args:
            file_path: Path to video file in storage
            expiration_minutes: How long the URL should be valid
        
        Returns:
            Signed streaming URL
        """
        return self.generate_download_url(file_path, expiration_minutes)
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from Firebase Storage
        
        Args:
            file_path: Path to file in storage
        
        Returns:
            True if deleted successfully
        """
        try:
            blob = self.bucket.blob(file_path)
            blob.delete()
            logger.info(f"Deleted file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {e}")
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage
        
        Args:
            file_path: Path to check
        
        Returns:
            True if file exists
        """
        try:
            blob = self.bucket.blob(file_path)
            return blob.exists()
        except Exception as e:
            logger.error(f"Error checking file existence {file_path}: {e}")
            return False
    
    def get_file_metadata(self, file_path: str) -> Optional[dict]:
        """
        Get metadata for a file
        
        Args:
            file_path: Path to file
        
        Returns:
            Dictionary of metadata or None
        """
        try:
            blob = self.bucket.blob(file_path)
            blob.reload()
            
            return {
                'name': blob.name,
                'size': blob.size,
                'content_type': blob.content_type,
                'created': blob.time_created,
                'updated': blob.updated,
                'md5_hash': blob.md5_hash,
            }
        except Exception as e:
            logger.error(f"Error getting metadata for {file_path}: {e}")
            return None
    
    def _generate_file_path(
        self,
        file_type: str,
        content_type: str,
        user_id: int
    ) -> str:
        """
        Generate a unique file path in storage
        
        Format: {type}/{timestamp_prefix}/{unique_id}.{extension}
        """
        import time
        
        # Get file extension from content type
        extension = mimetypes.guess_extension(content_type) or ''
        
        # Generate unique ID
        unique_id = uuid.uuid4().hex
        
        # Create timestamp prefix (for better organization and lifecycle rules)
        timestamp_prefix = str(int(time.time()))[:8]  # YYYYMMDD format approx
        
        # Map file types to storage paths
        path_map = {
            'video': 'videos',
            'resource': 'resources',
            'thumbnail': 'thumbnails',
            'lesson': 'lesson-plans'
        }
        
        base_path = path_map.get(file_type, 'uploads')
        
        # Construct path: videos/20250118/abc123def456.mp4
        file_path = f"{base_path}/{timestamp_prefix}/{unique_id}{extension}"
        
        return file_path
    
    def _get_allowed_content_types(self, file_type: str) -> list:
        """Get allowed MIME types for each file type"""
        type_map = {
            'video': [
                'video/mp4',
                'video/quicktime',
                'video/x-msvideo',
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
            ],
            'thumbnail': [
                'image/jpeg',
                'image/png',
                'image/webp',
            ],
            'lesson': [
                'application/pdf',
            ]
        }
        return type_map.get(file_type, [])
    
    def _get_max_file_size(self, file_type: str) -> int:
        """Get maximum file size in bytes for each file type"""
        size_map = {
            'video': 500 * 1024 * 1024,      # 500 MB
            'resource': 50 * 1024 * 1024,    # 50 MB
            'thumbnail': 10 * 1024 * 1024,   # 10 MB
            'lesson': 10 * 1024 * 1024,      # 10 MB
        }
        return size_map.get(file_type, 10 * 1024 * 1024)


# Singleton instance
_storage_service = None


def get_storage_service() -> FirebaseStorageService:
    """
    Get or create the Firebase Storage service singleton
    
    Returns:
        FirebaseStorageService instance
    """
    global _storage_service
    if _storage_service is None:
        _storage_service = FirebaseStorageService()
    return _storage_service


























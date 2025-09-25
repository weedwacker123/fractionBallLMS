import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from accounts.models import School
from .models import VideoAsset, Resource, Playlist, PlaylistItem
from .services import FirebaseStorageService

User = get_user_model()


class ContentModelsTest(TestCase):
    """Test content models"""
    
    def setUp(self):
        self.school = School.objects.create(name="Test School", domain="test")
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@test.edu',
            firebase_uid='teacher1_uid',
            role='TEACHER',
            school=self.school
        )
    
    def test_video_asset_creation(self):
        """Test VideoAsset model creation and properties"""
        video = VideoAsset.objects.create(
            title="Test Video",
            description="Test description",
            grade="3",
            topic="fractions_basics",
            tags=["visual", "interactive"],
            duration=300,  # 5 minutes
            file_size=100000000,  # 100MB
            storage_uri="https://storage.googleapis.com/test.mp4",
            owner=self.teacher,
            school=self.school,
            status='PUBLISHED'
        )
        
        self.assertEqual(video.owner, self.teacher)
        self.assertEqual(video.school, self.school)
        self.assertTrue(video.is_published)
        self.assertEqual(video.duration_formatted, "05:00")
        self.assertEqual(video.file_size_formatted, "95.4 MB")
    
    def test_playlist_with_items(self):
        """Test Playlist model with items"""
        playlist = Playlist.objects.create(
            name="Test Playlist",
            owner=self.teacher,
            school=self.school
        )
        
        video = VideoAsset.objects.create(
            title="Test Video",
            duration=300,
            storage_uri="https://storage.googleapis.com/test.mp4",
            owner=self.teacher,
            school=self.school,
            grade="3",
            topic="fractions_basics"
        )
        
        PlaylistItem.objects.create(
            playlist=playlist,
            video_asset=video,
            order=1
        )
        
        self.assertEqual(playlist.video_count, 1)
        self.assertEqual(playlist.total_duration, 300)


class FirebaseStorageServiceTest(TestCase):
    """Test Firebase Storage service"""
    
    def setUp(self):
        self.service = FirebaseStorageService()
    
    def test_video_file_validation(self):
        """Test video file validation"""
        # Valid video should pass
        result = self.service.validate_file(
            'test.mp4', 
            100 * 1024 * 1024,  # 100MB
            'video/mp4',
            'video'
        )
        self.assertTrue(result)
    
    def test_video_download_prevention(self):
        """Test that videos cannot get download URLs"""
        with self.assertRaises(Exception):
            self.service.generate_download_url('videos/2024/01/01/test.mp4')


class ContentAPITest(APITestCase):
    """Test content API endpoints"""
    
    def setUp(self):
        self.school = School.objects.create(name="Test School", domain="test")
        self.teacher = User.objects.create_user(
            username='teacher1',
            email='teacher1@test.edu',
            firebase_uid='teacher1_uid',
            role='TEACHER',
            school=self.school
        )
        
        self.video = VideoAsset.objects.create(
            title="Test Video",
            storage_uri="https://storage.googleapis.com/test.mp4",
            owner=self.teacher,
            school=self.school,
            grade="3",
            topic="fractions_basics",
            status='PUBLISHED'
        )
    
    def test_unauthenticated_access(self):
        """Test that endpoints require authentication"""
        response = self.client.get('/api/videos/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.post('/api/uploads/sign/', {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
import pytest
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from firebase_admin import auth
from accounts.models import School, User
from accounts.authentication import FirebaseAuthentication
from accounts.permissions import IsAdmin, IsSchoolAdmin, IsTeacher
import factory

User = get_user_model()


class SchoolFactory(factory.django.DjangoModelFactory):
    """Factory for School model"""
    class Meta:
        model = School
    
    name = factory.Sequence(lambda n: f"School {n}")
    domain = factory.Sequence(lambda n: f"school{n}")
    is_active = True


class UserFactory(factory.django.DjangoModelFactory):
    """Factory for User model"""
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    firebase_uid = factory.Sequence(lambda n: f"firebase_uid_{n}")
    school = factory.SubFactory(SchoolFactory)
    role = User.Role.TEACHER
    is_active = True


class SchoolModelTest(TestCase):
    """Test School model"""
    
    def test_school_creation(self):
        """Test school creation and string representation"""
        school = SchoolFactory(name="Test School", domain="test-school")
        self.assertEqual(str(school), "Test School")
        self.assertTrue(school.is_active)
        self.assertIsNotNone(school.created_at)
    
    def test_school_domain_unique(self):
        """Test school domain uniqueness"""
        SchoolFactory(domain="unique-domain")
        
        with self.assertRaises(Exception):
            SchoolFactory(domain="unique-domain")


class UserModelTest(TestCase):
    """Test User model"""
    
    def test_user_creation(self):
        """Test user creation with all roles"""
        school = SchoolFactory()
        
        # Test teacher
        teacher = UserFactory(school=school, role=User.Role.TEACHER)
        self.assertTrue(teacher.is_teacher)
        self.assertFalse(teacher.is_school_admin)
        self.assertFalse(teacher.is_admin)
        
        # Test school admin
        school_admin = UserFactory(school=school, role=User.Role.SCHOOL_ADMIN)
        self.assertTrue(school_admin.is_school_admin)
        self.assertFalse(school_admin.is_admin)
        
        # Test system admin
        admin = UserFactory(school=school, role=User.Role.ADMIN)
        self.assertTrue(admin.is_admin)
    
    def test_user_can_manage_school(self):
        """Test school management permissions"""
        school1 = SchoolFactory()
        school2 = SchoolFactory()
        
        admin = UserFactory(role=User.Role.ADMIN, school=school1)
        school_admin = UserFactory(role=User.Role.SCHOOL_ADMIN, school=school1)
        teacher = UserFactory(role=User.Role.TEACHER, school=school1)
        
        # Admin can manage any school
        self.assertTrue(admin.can_manage_school(school1))
        self.assertTrue(admin.can_manage_school(school2))
        
        # School admin can only manage their school
        self.assertTrue(school_admin.can_manage_school(school1))
        self.assertFalse(school_admin.can_manage_school(school2))
        
        # Teacher cannot manage any school
        self.assertFalse(teacher.can_manage_school(school1))
        self.assertFalse(teacher.can_manage_school(school2))
    
    def test_firebase_uid_unique(self):
        """Test Firebase UID uniqueness"""
        UserFactory(firebase_uid="unique_uid")
        
        with self.assertRaises(Exception):
            UserFactory(firebase_uid="unique_uid")


class FirebaseAuthenticationTest(TestCase):
    """Test Firebase authentication"""
    
    def setUp(self):
        self.auth = FirebaseAuthentication()
        self.school = SchoolFactory()
        self.user = UserFactory(firebase_uid="test_firebase_uid", school=self.school)
    
    @patch('accounts.authentication.auth.verify_id_token')
    def test_valid_firebase_token(self, mock_verify):
        """Test authentication with valid Firebase token"""
        # Mock Firebase token verification
        mock_verify.return_value = {
            'uid': 'test_firebase_uid',
            'email': 'test@example.com',
            'name': 'Test User'
        }
        
        # Create mock request
        request = MagicMock()
        request.META = {'HTTP_AUTHORIZATION': 'Bearer valid_token'}
        
        # Test authentication
        result = self.auth.authenticate(request)
        
        self.assertIsNotNone(result)
        authenticated_user, token = result
        self.assertEqual(authenticated_user.firebase_uid, 'test_firebase_uid')
        self.assertEqual(token, 'valid_token')
    
    @patch('accounts.authentication.auth.verify_id_token')
    def test_invalid_firebase_token(self, mock_verify):
        """Test authentication with invalid Firebase token"""
        # Mock Firebase token verification to raise exception
        mock_verify.side_effect = auth.InvalidIdTokenError('Invalid token')
        
        # Create mock request
        request = MagicMock()
        request.META = {'HTTP_AUTHORIZATION': 'Bearer invalid_token'}
        
        # Test authentication should raise exception
        with self.assertRaises(Exception):
            self.auth.authenticate(request)
    
    def test_missing_authorization_header(self):
        """Test authentication without authorization header"""
        request = MagicMock()
        request.META = {}
        
        result = self.auth.authenticate(request)
        self.assertIsNone(result)
    
    def test_malformed_authorization_header(self):
        """Test authentication with malformed authorization header"""
        request = MagicMock()
        request.META = {'HTTP_AUTHORIZATION': 'InvalidFormat token'}
        
        result = self.auth.authenticate(request)
        self.assertIsNone(result)
    
    @patch('accounts.authentication.auth.verify_id_token')
    def test_user_not_found(self, mock_verify):
        """Test authentication when user doesn't exist in database"""
        # Mock Firebase token verification
        mock_verify.return_value = {
            'uid': 'nonexistent_firebase_uid',
            'email': 'nonexistent@example.com',
            'name': 'Nonexistent User'
        }
        
        # Create mock request
        request = MagicMock()
        request.META = {'HTTP_AUTHORIZATION': 'Bearer valid_token'}
        
        # Test authentication should raise exception
        with self.assertRaises(Exception):
            self.auth.authenticate(request)


class PermissionsTest(TestCase):
    """Test custom permissions"""
    
    def setUp(self):
        self.school = SchoolFactory()
        self.admin = UserFactory(role=User.Role.ADMIN, school=self.school)
        self.school_admin = UserFactory(role=User.Role.SCHOOL_ADMIN, school=self.school)
        self.teacher = UserFactory(role=User.Role.TEACHER, school=self.school)
        self.other_school = SchoolFactory()
        self.other_teacher = UserFactory(role=User.Role.TEACHER, school=self.other_school)
    
    def test_is_admin_permission(self):
        """Test IsAdmin permission"""
        permission = IsAdmin()
        
        # Create mock requests
        admin_request = MagicMock()
        admin_request.user = self.admin
        
        teacher_request = MagicMock()
        teacher_request.user = self.teacher
        
        # Test permissions
        self.assertTrue(permission.has_permission(admin_request, None))
        self.assertFalse(permission.has_permission(teacher_request, None))
    
    def test_is_school_admin_permission(self):
        """Test IsSchoolAdmin permission"""
        permission = IsSchoolAdmin()
        
        # Create mock requests
        admin_request = MagicMock()
        admin_request.user = self.admin
        
        school_admin_request = MagicMock()
        school_admin_request.user = self.school_admin
        
        teacher_request = MagicMock()
        teacher_request.user = self.teacher
        
        # Test permissions
        self.assertTrue(permission.has_permission(admin_request, None))
        self.assertTrue(permission.has_permission(school_admin_request, None))
        self.assertFalse(permission.has_permission(teacher_request, None))
    
    def test_is_teacher_permission(self):
        """Test IsTeacher permission"""
        permission = IsTeacher()
        
        # Create mock requests for all roles
        admin_request = MagicMock()
        admin_request.user = self.admin
        
        school_admin_request = MagicMock()
        school_admin_request.user = self.school_admin
        
        teacher_request = MagicMock()
        teacher_request.user = self.teacher
        
        # All roles should have teacher permission
        self.assertTrue(permission.has_permission(admin_request, None))
        self.assertTrue(permission.has_permission(school_admin_request, None))
        self.assertTrue(permission.has_permission(teacher_request, None))


class APIEndpointsTest(APITestCase):
    """Test API endpoints"""
    
    def setUp(self):
        self.school = SchoolFactory()
        self.admin = UserFactory(role=User.Role.ADMIN, school=self.school)
        self.teacher = UserFactory(role=User.Role.TEACHER, school=self.school)
    
    def test_health_check_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/healthz/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
    
    @patch('accounts.authentication.auth.verify_id_token')
    def test_me_endpoint_authenticated(self, mock_verify):
        """Test /api/me/ endpoint with authenticated user"""
        # Mock Firebase token verification
        mock_verify.return_value = {
            'uid': self.teacher.firebase_uid,
            'email': self.teacher.email,
            'name': self.teacher.get_full_name()
        }
        
        # Make authenticated request
        self.client.credentials(HTTP_AUTHORIZATION='Bearer valid_token')
        response = self.client.get('/api/me/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.teacher.id)
        self.assertEqual(response.data['email'], self.teacher.email)
        self.assertIn('permissions', response.data)
    
    def test_me_endpoint_unauthenticated(self):
        """Test /api/me/ endpoint without authentication"""
        response = self.client.get('/api/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.shortcuts import render
from accounts.models import School
from accounts.permissions import IsAdmin, IsSchoolAdmin, CanManageSchool
from .serializers import (
    UserSerializer, UserCreateSerializer, MeSerializer,
    SchoolSerializer
)

User = get_user_model()


def home(request):
    """Home page view"""
    return render(request, 'base.html')


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def health_check(request):
    """Health check endpoint"""
    return Response({
        'status': 'healthy',
        'message': 'Fraction Ball LMS API is running'
    })


class MeView(generics.RetrieveUpdateAPIView):
    """
    Current user profile endpoint
    GET /api/me/ - Get current user profile
    PUT/PATCH /api/me/ - Update current user profile
    """
    serializer_class = MeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class SchoolViewSet(ModelViewSet):
    """
    ViewSet for School management (Admin only)
    """
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
    search_fields = ['name', 'domain']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Optimize queryset with prefetch"""
        return School.objects.prefetch_related('user_set').all()


class UserViewSet(ModelViewSet):
    """
    ViewSet for User management
    - System admins: can manage all users
    - School admins: can manage users in their school only
    """
    queryset = User.objects.select_related('school').all()
    serializer_class = UserSerializer
    permission_classes = [IsSchoolAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'school', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'created_at']
    ordering = ['last_name', 'first_name']
    
    def get_queryset(self):
        """Filter users based on requester's role"""
        queryset = User.objects.select_related('school').all()
        
        # School admins can only see users from their school
        if not self.request.user.is_admin and self.request.user.is_school_admin:
            queryset = queryset.filter(school=self.request.user.school)
        
        return queryset
    
    def get_serializer_class(self):
        """Use different serializer for creation"""
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer
    
    def perform_create(self, serializer):
        """Custom user creation logic"""
        # School admins can only create users in their school
        if not self.request.user.is_admin and self.request.user.is_school_admin:
            serializer.save(school=self.request.user.school)
        else:
            serializer.save()
    
    def perform_update(self, serializer):
        """Custom user update logic"""
        # Prevent school admins from changing school assignment
        if not self.request.user.is_admin and self.request.user.is_school_admin:
            # Remove school from validated_data if present
            if 'school' in serializer.validated_data:
                serializer.validated_data.pop('school')
        
        serializer.save()


class SchoolUserListView(generics.ListAPIView):
    """
    List users for a specific school
    GET /api/schools/{id}/users/
    """
    serializer_class = UserSerializer
    permission_classes = [CanManageSchool]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'is_active']
    
    def get_queryset(self):
        """Get users for the specified school"""
        school_id = self.kwargs['school_id']
        return User.objects.filter(school_id=school_id).select_related('school')
"""
Admin operations views for user management and system administration
"""
from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.db import models, transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from .permissions import IsAdmin, IsSchoolAdmin
from .models import School
from .serializers import UserSerializer, SchoolSerializer
from content.models import AuditLog
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class AdminUserViewSet(ModelViewSet):
    """
    Admin-only user management with search, filtering, and role changes
    """
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'is_active', 'school']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering_fields = ['username', 'email', 'created_at', 'last_login']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Get all users for admin, school-scoped for school admins"""
        user = self.request.user
        
        if user.is_admin:
            # System admins see all users
            return User.objects.select_related('school').all()
        elif user.is_school_admin:
            # School admins only see users from their school
            return User.objects.select_related('school').filter(
                school=user.school
            )
        else:
            # Regular users shouldn't access this endpoint
            return User.objects.none()
    
    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        """
        Change user role (admin only for system-wide, school admin for school users)
        POST /api/admin/users/{id}/change_role/
        """
        target_user = self.get_object()
        new_role = request.data.get('role')
        
        if not new_role or new_role not in [choice[0] for choice in User.Role.choices]:
            return Response(
                {'error': 'Valid role is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Permission checks
        if request.user.is_school_admin:
            # School admins can only manage users in their school
            if target_user.school != request.user.school:
                return Response(
                    {'error': 'Cannot manage users outside your school'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # School admins cannot create system admins
            if new_role == User.Role.ADMIN:
                return Response(
                    {'error': 'Cannot assign system admin role'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Cannot change own role
        if target_user == request.user:
            return Response(
                {'error': 'Cannot change your own role'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_role = target_user.role
        target_user.role = new_role
        target_user.save()
        
        # Log role change
        AuditLog.objects.create(
            action='USER_ROLE_CHANGED',
            user=request.user,
            metadata={
                'target_user_id': str(target_user.id),
                'target_username': target_user.username,
                'old_role': old_role,
                'new_role': new_role,
                'school': target_user.school.name if target_user.school else None
            },
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'message': f'Role changed from {old_role} to {new_role}',
            'user': UserSerializer(target_user).data
        })
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """
        Activate user account
        POST /api/admin/users/{id}/activate/
        """
        target_user = self.get_object()
        
        # Permission checks for school admins
        if request.user.is_school_admin and target_user.school != request.user.school:
            return Response(
                {'error': 'Cannot manage users outside your school'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        if target_user.is_active:
            return Response(
                {'message': 'User is already active'}, 
                status=status.HTTP_200_OK
            )
        
        target_user.is_active = True
        target_user.save()
        
        # Log activation
        AuditLog.objects.create(
            action='USER_ACTIVATED',
            user=request.user,
            metadata={
                'target_user_id': str(target_user.id),
                'target_username': target_user.username,
                'school': target_user.school.name if target_user.school else None
            },
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'message': 'User activated successfully',
            'user': UserSerializer(target_user).data
        })
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """
        Deactivate user account
        POST /api/admin/users/{id}/deactivate/
        """
        target_user = self.get_object()
        
        # Permission checks for school admins
        if request.user.is_school_admin and target_user.school != request.user.school:
            return Response(
                {'error': 'Cannot manage users outside your school'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Cannot deactivate self
        if target_user == request.user:
            return Response(
                {'error': 'Cannot deactivate your own account'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not target_user.is_active:
            return Response(
                {'message': 'User is already inactive'}, 
                status=status.HTTP_200_OK
            )
        
        target_user.is_active = False
        target_user.save()
        
        # Log deactivation
        AuditLog.objects.create(
            action='USER_DEACTIVATED',
            user=request.user,
            metadata={
                'target_user_id': str(target_user.id),
                'target_username': target_user.username,
                'reason': request.data.get('reason', 'No reason provided'),
                'school': target_user.school.name if target_user.school else None
            },
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'message': 'User deactivated successfully',
            'user': UserSerializer(target_user).data
        })
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """
        Advanced user search with filters
        GET /api/admin/users/search/?q=query&role=TEACHER&school=1&active=true
        """
        queryset = self.get_queryset()
        
        # Search query
        query = request.query_params.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(username__icontains=query) |
                Q(email__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query)
            )
        
        # Role filter
        role = request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # School filter
        school_id = request.query_params.get('school')
        if school_id:
            try:
                queryset = queryset.filter(school_id=school_id)
            except ValueError:
                pass
        
        # Active filter
        active = request.query_params.get('active')
        if active is not None:
            is_active = active.lower() in ('true', '1', 'yes')
            queryset = queryset.filter(is_active=is_active)
        
        # Pagination
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        paginator = Paginator(queryset, page_size)
        page_number = request.query_params.get('page', 1)
        page = paginator.get_page(page_number)
        
        # Serialize results
        serializer = UserSerializer(page.object_list, many=True)
        
        return Response({
            'results': serializer.data,
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page.number,
            'has_next': page.has_next(),
            'has_previous': page.has_previous(),
        })
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SchoolAdminViewSet(ModelViewSet):
    """
    School management for system admins
    """
    serializer_class = SchoolSerializer
    permission_classes = [IsAdmin]  # Only system admins
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_active']
    search_fields = ['name', 'domain']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """All schools for system admins"""
        return School.objects.all()
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """
        Get users for a specific school
        GET /api/admin/schools/{id}/users/
        """
        school = self.get_object()
        users = User.objects.filter(school=school).select_related('school')
        
        # Apply filters
        role = request.query_params.get('role')
        if role:
            users = users.filter(role=role)
        
        active = request.query_params.get('active')
        if active is not None:
            is_active = active.lower() in ('true', '1', 'yes')
            users = users.filter(is_active=is_active)
        
        # Pagination
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        paginator = Paginator(users, page_size)
        page_number = request.query_params.get('page', 1)
        page = paginator.get_page(page_number)
        
        serializer = UserSerializer(page.object_list, many=True)
        
        return Response({
            'school': SchoolSerializer(school).data,
            'users': serializer.data,
            'count': paginator.count,
            'num_pages': paginator.num_pages,
            'current_page': page.number,
        })
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """
        Get statistics for a specific school
        GET /api/admin/schools/{id}/stats/
        """
        school = self.get_object()
        
        # User statistics
        user_stats = User.objects.filter(school=school).aggregate(
            total_users=Count('id'),
            active_users=Count('id', filter=Q(is_active=True)),
            teachers=Count('id', filter=Q(role=User.Role.TEACHER)),
            school_admins=Count('id', filter=Q(role=User.Role.SCHOOL_ADMIN)),
        )
        
        # Content statistics
        from content.models import VideoAsset, Resource, Playlist
        content_stats = {
            'total_videos': VideoAsset.objects.filter(school=school).count(),
            'published_videos': VideoAsset.objects.filter(school=school, status='PUBLISHED').count(),
            'total_resources': Resource.objects.filter(school=school).count(),
            'total_playlists': Playlist.objects.filter(school=school).count(),
        }
        
        # Recent activity (last 30 days)
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        activity_stats = {
            'recent_videos': VideoAsset.objects.filter(
                school=school, 
                created_at__gte=thirty_days_ago
            ).count(),
            'recent_logins': User.objects.filter(
                school=school, 
                last_login__gte=thirty_days_ago
            ).count(),
        }
        
        return Response({
            'school': SchoolSerializer(school).data,
            'user_stats': user_stats,
            'content_stats': content_stats,
            'activity_stats': activity_stats,
            'generated_at': timezone.now().isoformat(),
        })


@api_view(['GET'])
@permission_classes([IsAdmin])
def admin_dashboard(request):
    """
    System admin dashboard with platform-wide statistics
    GET /api/admin/dashboard/
    """
    try:
        # Platform statistics
        total_schools = School.objects.count()
        active_schools = School.objects.filter(is_active=True).count()
        
        # User statistics
        user_stats = User.objects.aggregate(
            total_users=Count('id'),
            active_users=Count('id', filter=Q(is_active=True)),
            system_admins=Count('id', filter=Q(role=User.Role.ADMIN)),
            school_admins=Count('id', filter=Q(role=User.Role.SCHOOL_ADMIN)),
            teachers=Count('id', filter=Q(role=User.Role.TEACHER)),
        )
        
        # Content statistics
        from content.models import VideoAsset, Resource, Playlist
        content_stats = {
            'total_videos': VideoAsset.objects.count(),
            'published_videos': VideoAsset.objects.filter(status='PUBLISHED').count(),
            'pending_videos': VideoAsset.objects.filter(status='PENDING').count(),
            'total_resources': Resource.objects.count(),
            'total_playlists': Playlist.objects.count(),
        }
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        
        recent_activity = {
            'new_users': User.objects.filter(created_at__gte=week_ago).count(),
            'new_videos': VideoAsset.objects.filter(created_at__gte=week_ago).count(),
            'recent_logins': User.objects.filter(last_login__gte=week_ago).count(),
        }
        
        # Top schools by content
        top_schools = School.objects.annotate(
            video_count=Count('videoasset'),
            user_count=Count('user')
        ).filter(
            is_active=True
        ).order_by('-video_count')[:5]
        
        top_schools_data = []
        for school in top_schools:
            top_schools_data.append({
                'id': school.id,
                'name': school.name,
                'domain': school.domain,
                'video_count': school.video_count,
                'user_count': school.user_count,
            })
        
        # Recent audit logs
        recent_logs = AuditLog.objects.select_related('user').order_by('-created_at')[:10]
        recent_logs_data = []
        for log in recent_logs:
            recent_logs_data.append({
                'action': log.get_action_display(),
                'user': log.user.get_full_name(),
                'created_at': log.created_at,
                'metadata': log.metadata
            })
        
        dashboard_data = {
            'platform_stats': {
                'total_schools': total_schools,
                'active_schools': active_schools,
            },
            'user_stats': user_stats,
            'content_stats': content_stats,
            'recent_activity': recent_activity,
            'top_schools': top_schools_data,
            'recent_audit_logs': recent_logs_data,
            'generated_at': timezone.now().isoformat(),
        }
        
        return Response(dashboard_data)
        
    except Exception as e:
        logger.error(f"Admin dashboard generation failed: {e}")
        return Response(
            {'error': 'Failed to generate dashboard', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

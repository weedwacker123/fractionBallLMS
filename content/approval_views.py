"""
Content approval workflow views
Draft → Pending → Published/Rejected
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
from django.db.models import Q, Count
from accounts.permissions import require_permission
from .models import VideoAsset, Resource, AuditLog
from .serializers import VideoAssetSerializer, ResourceSerializer
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class ContentApprovalViewSet(ModelViewSet):
    """
    Content approval workflow management for school admins and system admins
    """
    serializer_class = VideoAssetSerializer
    permission_classes = [require_permission('content.manage')]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'grade', 'topic', 'owner']
    search_fields = ['title', 'description']
    ordering_fields = ['title', 'created_at', 'submitted_at']
    ordering = ['-submitted_at', '-created_at']

    def get_permissions(self):
        if self.action in ['approve', 'reject', 'pending', 'approval_stats']:
            permission_classes = [require_permission('content.approve')]
        else:
            permission_classes = [require_permission('content.manage')]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Get content for approval based on user permissions"""
        user = self.request.user
        
        if user.can('schools.manage'):
            # System admins see all content
            return VideoAsset.objects.select_related(
                'owner', 'school', 'reviewed_by'
            ).all()
        elif user.can('content.approve'):
            # School admins only see content from their school
            return VideoAsset.objects.select_related(
                'owner', 'school', 'reviewed_by'
            ).filter(school=user.school)
        else:
            return VideoAsset.objects.none()
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """
        Get all pending content for review
        GET /api/approval/videos/pending/
        """
        queryset = self.get_queryset().filter(status='PENDING')
        
        # Apply additional filters
        queryset = self.filter_queryset(queryset)
        
        # Pagination
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def submit_for_review(self, request, pk=None):
        """
        Submit content for review (Draft → Pending)
        POST /api/approval/videos/{id}/submit_for_review/
        """
        video = self.get_object()
        
        # Only owners can submit their own content
        if video.owner != request.user and not request.user.can('content.approve'):
            return Response(
                {'error': 'Only the content owner can submit for review'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check current status
        if video.status != 'DRAFT':
            return Response(
                {'error': f'Content must be in DRAFT status to submit for review. Current status: {video.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate content completeness
        validation_errors = []
        if not video.title or len(video.title.strip()) < 3:
            validation_errors.append('Title must be at least 3 characters')
        if not video.description or len(video.description.strip()) < 10:
            validation_errors.append('Description must be at least 10 characters')
        if not video.grade:
            validation_errors.append('Grade level is required')
        if not video.topic:
            validation_errors.append('Topic is required')
        
        if validation_errors:
            return Response(
                {'error': 'Content validation failed', 'details': validation_errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Submit for review
        video.status = 'PENDING'
        video.submitted_at = timezone.now()
        video.save()
        
        # Log submission
        AuditLog.objects.create(
            action='CONTENT_SUBMITTED',
            user=request.user,
            metadata={
                'content_id': str(video.id),
                'content_title': video.title,
                'content_type': 'video',
                'previous_status': 'DRAFT',
                'new_status': 'PENDING'
            },
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'message': 'Content submitted for review successfully',
            'video': VideoAssetSerializer(video).data
        })
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve content (Pending → Published)
        POST /api/approval/videos/{id}/approve/
        """
        video = self.get_object()
        
        # Only school admins and system admins can approve
        if not request.user.can('content.approve'):
            return Response(
                {'error': 'Insufficient permissions to approve content'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # School admins can only approve content from their school
        if not request.user.can('schools.manage') and video.school != request.user.school:
            return Response(
                {'error': 'Cannot approve content from other schools'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check current status
        if video.status != 'PENDING':
            return Response(
                {'error': f'Content must be PENDING to approve. Current status: {video.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cannot approve own content
        if video.owner == request.user:
            return Response(
                {'error': 'Cannot approve your own content'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        approval_notes = request.data.get('notes', '')
        
        # Approve content
        video.status = 'PUBLISHED'
        video.reviewed_by = request.user
        video.reviewed_at = timezone.now()
        video.review_notes = approval_notes
        video.save()
        
        # Log approval
        AuditLog.objects.create(
            action='CONTENT_APPROVED',
            user=request.user,
            metadata={
                'content_id': str(video.id),
                'content_title': video.title,
                'content_type': 'video',
                'content_owner': video.owner.get_full_name(),
                'previous_status': 'PENDING',
                'new_status': 'PUBLISHED',
                'approval_notes': approval_notes
            },
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'message': 'Content approved and published successfully',
            'video': VideoAssetSerializer(video).data
        })
    
    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject content (Pending → Rejected)
        POST /api/approval/videos/{id}/reject/
        """
        video = self.get_object()
        
        # Only school admins and system admins can reject
        if not request.user.can('content.approve'):
            return Response(
                {'error': 'Insufficient permissions to reject content'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # School admins can only reject content from their school
        if not request.user.can('schools.manage') and video.school != request.user.school:
            return Response(
                {'error': 'Cannot reject content from other schools'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check current status
        if video.status != 'PENDING':
            return Response(
                {'error': f'Content must be PENDING to reject. Current status: {video.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Cannot reject own content
        if video.owner == request.user:
            return Response(
                {'error': 'Cannot reject your own content'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        rejection_reason = request.data.get('reason', '')
        if not rejection_reason or len(rejection_reason.strip()) < 10:
            return Response(
                {'error': 'Rejection reason is required (minimum 10 characters)'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Reject content
        video.status = 'REJECTED'
        video.reviewed_by = request.user
        video.reviewed_at = timezone.now()
        video.review_notes = rejection_reason
        video.save()
        
        # Log rejection
        AuditLog.objects.create(
            action='CONTENT_REJECTED',
            user=request.user,
            metadata={
                'content_id': str(video.id),
                'content_title': video.title,
                'content_type': 'video',
                'content_owner': video.owner.get_full_name(),
                'previous_status': 'PENDING',
                'new_status': 'REJECTED',
                'rejection_reason': rejection_reason
            },
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'message': 'Content rejected successfully',
            'video': VideoAssetSerializer(video).data
        })
    
    @action(detail=True, methods=['post'])
    def return_to_draft(self, request, pk=None):
        """
        Return content to draft status (Rejected → Draft)
        POST /api/approval/videos/{id}/return_to_draft/
        """
        video = self.get_object()
        
        # Only content owner can return to draft
        if video.owner != request.user:
            return Response(
                {'error': 'Only the content owner can return content to draft'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check current status
        if video.status not in ['REJECTED', 'PENDING']:
            return Response(
                {'error': f'Content must be REJECTED or PENDING to return to draft. Current status: {video.status}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return to draft
        old_status = video.status
        video.status = 'DRAFT'
        video.submitted_at = None
        video.reviewed_by = None
        video.reviewed_at = None
        video.review_notes = ''
        video.save()
        
        # Log status change
        AuditLog.objects.create(
            action='CONTENT_RETURNED_TO_DRAFT',
            user=request.user,
            metadata={
                'content_id': str(video.id),
                'content_title': video.title,
                'content_type': 'video',
                'previous_status': old_status,
                'new_status': 'DRAFT'
            },
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'message': 'Content returned to draft status',
            'video': VideoAssetSerializer(video).data
        })
    
    @action(detail=False, methods=['get'])
    def approval_stats(self, request):
        """
        Get approval workflow statistics
        GET /api/approval/videos/approval_stats/
        """
        queryset = self.get_queryset()
        
        # Status breakdown
        status_stats = queryset.aggregate(
            total_content=Count('id'),
            draft_count=Count('id', filter=Q(status='DRAFT')),
            pending_count=Count('id', filter=Q(status='PENDING')),
            published_count=Count('id', filter=Q(status='PUBLISHED')),
            rejected_count=Count('id', filter=Q(status='REJECTED')),
        )
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        
        recent_activity = queryset.filter(
            models.Q(submitted_at__gte=week_ago) | 
            models.Q(reviewed_at__gte=week_ago)
        ).aggregate(
            recent_submissions=Count('id', filter=Q(submitted_at__gte=week_ago)),
            recent_approvals=Count('id', filter=Q(reviewed_at__gte=week_ago, status='PUBLISHED')),
            recent_rejections=Count('id', filter=Q(reviewed_at__gte=week_ago, status='REJECTED')),
        )
        
        # Top contributors (by submitted content)
        top_contributors = User.objects.filter(
            videoasset__in=queryset,
            videoasset__submitted_at__isnull=False
        ).annotate(
            submission_count=Count('videoasset', filter=Q(videoasset__submitted_at__isnull=False))
        ).order_by('-submission_count')[:5]
        
        contributors_data = []
        for user in top_contributors:
            contributors_data.append({
                'name': user.get_full_name(),
                'username': user.username,
                'submission_count': user.submission_count,
                'school': user.school.name if user.school else None
            })
        
        return Response({
            'status_breakdown': status_stats,
            'recent_activity': recent_activity,
            'top_contributors': contributors_data,
            'generated_at': timezone.now().isoformat(),
        })
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@api_view(['GET'])
@permission_classes([require_permission('content.manage')])
def my_content_status(request):
    """
    Get current user's content status overview
    GET /api/approval/my_content_status/
    """
    try:
        user = request.user
        
        # Get user's content by status
        my_videos = VideoAsset.objects.filter(owner=user)
        
        status_breakdown = my_videos.aggregate(
            total_content=Count('id'),
            draft_count=Count('id', filter=Q(status='DRAFT')),
            pending_count=Count('id', filter=Q(status='PENDING')),
            published_count=Count('id', filter=Q(status='PUBLISHED')),
            rejected_count=Count('id', filter=Q(status='REJECTED')),
        )
        
        # Recent submissions and reviews
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        
        recent_activity = {
            'recent_submissions': my_videos.filter(submitted_at__gte=week_ago).count(),
            'recent_reviews': my_videos.filter(reviewed_at__gte=week_ago).count(),
        }
        
        # Pending items that need attention
        pending_items = my_videos.filter(status='PENDING').order_by('-submitted_at')[:5]
        pending_data = VideoAssetSerializer(pending_items, many=True).data
        
        # Recently rejected items
        rejected_items = my_videos.filter(status='REJECTED').order_by('-reviewed_at')[:3]
        rejected_data = []
        for video in rejected_items:
            video_data = VideoAssetSerializer(video).data
            video_data['rejection_reason'] = video.review_notes
            video_data['reviewed_by_name'] = video.reviewed_by.get_full_name() if video.reviewed_by else None
            rejected_data.append(video_data)
        
        return Response({
            'status_breakdown': status_breakdown,
            'recent_activity': recent_activity,
            'pending_items': pending_data,
            'recently_rejected': rejected_data,
            'generated_at': timezone.now().isoformat(),
        })
        
    except Exception as e:
        logger.error(f"Content status overview failed for user {request.user.id}: {e}")
        return Response(
            {'error': 'Failed to generate content status overview', 'message': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )








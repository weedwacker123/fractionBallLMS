"""
System configuration views for branding, feature flags, and settings
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
from django.core.cache import cache
from accounts.permissions import IsAdmin
from .models import SystemConfig, FeatureFlag, ConfigChangeLog
from .serializers import SystemConfigSerializer, FeatureFlagSerializer, ConfigChangeLogSerializer
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class SystemConfigViewSet(ModelViewSet):
    """
    System configuration management (admin only)
    """
    serializer_class = SystemConfigSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['category', 'config_type', 'is_public', 'is_editable']
    search_fields = ['key', 'name', 'description']
    ordering_fields = ['name', 'category', 'updated_at']
    ordering = ['category', 'name']
    
    def get_queryset(self):
        """All configurations for admin users"""
        return SystemConfig.objects.all()
    
    def perform_update(self, serializer):
        """Log configuration changes"""
        old_instance = SystemConfig.objects.get(pk=serializer.instance.pk)
        old_value = old_instance.value
        
        # Save the updated instance
        instance = serializer.save(updated_by=self.request.user)
        
        # Log the change if value changed
        if old_value != instance.value:
            ConfigChangeLog.objects.create(
                config=instance,
                old_value=old_value,
                new_value=instance.value,
                change_reason=self.request.data.get('change_reason', ''),
                changed_by=self.request.user,
                ip_address=self.get_client_ip(self.request)
            )
            
            # Clear cache for this config
            cache.delete(f'config:{instance.key}')
            cache.delete('public_config')
    
    def perform_create(self, serializer):
        """Set creator and log creation"""
        instance = serializer.save(updated_by=self.request.user)
        
        # Log creation
        ConfigChangeLog.objects.create(
            config=instance,
            old_value='',
            new_value=instance.value,
            change_reason='Configuration created',
            changed_by=self.request.user,
            ip_address=self.get_client_ip(self.request)
        )
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """
        Get configurations grouped by category
        GET /api/config/system/by_category/
        """
        configs = self.get_queryset()
        
        # Group by category
        categories = {}
        for config in configs:
            category = config.category
            if category not in categories:
                categories[category] = []
            categories[category].append(SystemConfigSerializer(config).data)
        
        return Response({
            'categories': categories,
            'total_configs': configs.count()
        })
    
    @action(detail=True, methods=['get'])
    def change_history(self, request, pk=None):
        """
        Get change history for a configuration
        GET /api/config/system/{id}/change_history/
        """
        config = self.get_object()
        changes = ConfigChangeLog.objects.filter(config=config).select_related('changed_by')[:20]
        
        serializer = ConfigChangeLogSerializer(changes, many=True)
        return Response({
            'config': SystemConfigSerializer(config).data,
            'changes': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """
        Bulk update multiple configurations
        POST /api/config/system/bulk_update/
        Body: {"configs": [{"key": "key1", "value": "value1"}, ...]}
        """
        configs_data = request.data.get('configs', [])
        if not configs_data:
            return Response(
                {'error': 'configs array is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_configs = []
        errors = []
        
        with transaction.atomic():
            for config_data in configs_data:
                config_key = config_data.get('key')
                new_value = config_data.get('value')
                
                if not config_key:
                    errors.append({'error': 'key is required', 'data': config_data})
                    continue
                
                try:
                    config = SystemConfig.objects.get(key=config_key)
                    
                    # Check if editable
                    if not config.is_editable:
                        errors.append({'error': f'Configuration {config_key} is not editable', 'data': config_data})
                        continue
                    
                    old_value = config.value
                    config.value = str(new_value) if new_value is not None else ''
                    config.updated_by = request.user
                    config.save()
                    
                    # Log change
                    if old_value != config.value:
                        ConfigChangeLog.objects.create(
                            config=config,
                            old_value=old_value,
                            new_value=config.value,
                            change_reason=f'Bulk update: {request.data.get("reason", "")}',
                            changed_by=request.user,
                            ip_address=self.get_client_ip(request)
                        )
                        
                        # Clear cache
                        cache.delete(f'config:{config.key}')
                    
                    updated_configs.append(SystemConfigSerializer(config).data)
                    
                except SystemConfig.DoesNotExist:
                    errors.append({'error': f'Configuration {config_key} not found', 'data': config_data})
                except Exception as e:
                    errors.append({'error': f'Failed to update {config_key}: {str(e)}', 'data': config_data})
        
        # Clear public config cache if any public configs were updated
        if any(config.get('is_public') for config in updated_configs):
            cache.delete('public_config')
        
        return Response({
            'updated': updated_configs,
            'errors': errors,
            'total_updated': len(updated_configs),
            'total_errors': len(errors)
        })
    
    def get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FeatureFlagViewSet(ModelViewSet):
    """
    Feature flag management (admin only)
    """
    serializer_class = FeatureFlagSerializer
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_enabled', 'is_permanent']
    search_fields = ['name', 'display_name', 'description']
    ordering_fields = ['display_name', 'created_at', 'updated_at']
    ordering = ['display_name']
    
    def get_queryset(self):
        """All feature flags for admin users"""
        return FeatureFlag.objects.prefetch_related('applies_to_schools')
    
    def perform_update(self, serializer):
        """Log feature flag changes"""
        instance = serializer.save(updated_by=self.request.user)
        
        # Clear feature flag cache
        cache.delete(f'feature_flag:{instance.name}')
        cache.delete('feature_flags')
    
    def perform_create(self, serializer):
        """Set creator"""
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        """
        Toggle feature flag on/off
        POST /api/config/features/{id}/toggle/
        """
        feature_flag = self.get_object()
        
        if feature_flag.is_permanent:
            return Response(
                {'error': 'Cannot toggle permanent feature flag'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = feature_flag.is_enabled
        feature_flag.is_enabled = not feature_flag.is_enabled
        feature_flag.updated_by = request.user
        feature_flag.save()
        
        # Clear cache
        cache.delete(f'feature_flag:{feature_flag.name}')
        cache.delete('feature_flags')
        
        # Log change
        from content.models import AuditLog
        AuditLog.objects.create(
            action='FEATURE_FLAG_TOGGLED',
            user=request.user,
            metadata={
                'feature_flag_name': feature_flag.name,
                'old_status': old_status,
                'new_status': feature_flag.is_enabled,
                'display_name': feature_flag.display_name
            },
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'message': f'Feature flag {"enabled" if feature_flag.is_enabled else "disabled"}',
            'feature_flag': FeatureFlagSerializer(feature_flag).data
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
@permission_classes([permissions.AllowAny])  # Public endpoint
def public_config(request):
    """
    Get public configuration settings
    GET /api/public-config/
    """
    try:
        # Try to get from cache first
        cached_config = cache.get('public_config')
        if cached_config:
            return Response(cached_config)
        
        # Get public configurations
        public_configs = SystemConfig.objects.filter(is_public=True)
        
        config_data = {}
        for config in public_configs:
            # Organize by category
            category = config.category
            if category not in config_data:
                config_data[category] = {}
            
            # Use the typed value
            config_data[category][config.key] = config.get_typed_value()
        
        # Add feature flags that are public
        feature_flags = FeatureFlag.objects.filter(is_enabled=True)
        flags_data = {}
        for flag in feature_flags:
            flags_data[flag.name] = {
                'enabled': flag.is_enabled,
                'display_name': flag.display_name,
                'description': flag.description
            }
        
        response_data = {
            'config': config_data,
            'features': flags_data,
            'generated_at': timezone.now().isoformat(),
        }
        
        # Cache for 5 minutes
        cache.set('public_config', response_data, 300)
        
        return Response(response_data)
        
    except Exception as e:
        logger.error(f"Failed to generate public config: {e}")
        return Response(
            {'error': 'Failed to load configuration'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAdmin])
def config_dashboard(request):
    """
    Configuration management dashboard
    GET /api/config/dashboard/
    """
    try:
        # Configuration statistics
        config_stats = SystemConfig.objects.aggregate(
            total_configs=models.Count('id'),
            public_configs=models.Count('id', filter=models.Q(is_public=True)),
            editable_configs=models.Count('id', filter=models.Q(is_editable=True)),
        )
        
        # Feature flag statistics
        flag_stats = FeatureFlag.objects.aggregate(
            total_flags=models.Count('id'),
            enabled_flags=models.Count('id', filter=models.Q(is_enabled=True)),
            permanent_flags=models.Count('id', filter=models.Q(is_permanent=True)),
        )
        
        # Recent changes (last 7 days)
        from datetime import timedelta
        week_ago = timezone.now() - timedelta(days=7)
        
        recent_changes = ConfigChangeLog.objects.filter(
            changed_at__gte=week_ago
        ).select_related('config', 'changed_by').order_by('-changed_at')[:10]
        
        changes_data = []
        for change in recent_changes:
            changes_data.append({
                'config_name': change.config.name,
                'config_key': change.config.key,
                'old_value': change.old_value[:50] + '...' if len(change.old_value) > 50 else change.old_value,
                'new_value': change.new_value[:50] + '...' if len(change.new_value) > 50 else change.new_value,
                'changed_by': change.changed_by.get_full_name() if change.changed_by else 'System',
                'changed_at': change.changed_at,
            })
        
        # Configuration categories
        categories = SystemConfig.objects.values('category').annotate(
            count=models.Count('id')
        ).order_by('category')
        
        return Response({
            'config_stats': config_stats,
            'flag_stats': flag_stats,
            'recent_changes': changes_data,
            'categories': list(categories),
            'generated_at': timezone.now().isoformat(),
        })
        
    except Exception as e:
        logger.error(f"Config dashboard generation failed: {e}")
        return Response(
            {'error': 'Failed to generate dashboard'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )










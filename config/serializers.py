"""
Serializers for system configuration
"""
from rest_framework import serializers
from .models import SystemConfig, FeatureFlag, ConfigChangeLog


class SystemConfigSerializer(serializers.ModelSerializer):
    """Serializer for system configuration"""
    updated_by_name = serializers.SerializerMethodField()
    typed_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemConfig
        fields = [
            'id', 'key', 'value', 'config_type', 'name', 'description',
            'category', 'is_public', 'is_editable', 'validation_regex',
            'min_value', 'max_value', 'created_at', 'updated_at',
            'updated_by', 'updated_by_name', 'typed_value'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'updated_by']
    
    def get_updated_by_name(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name()
        return None
    
    def get_typed_value(self, obj):
        return obj.get_typed_value()


class FeatureFlagSerializer(serializers.ModelSerializer):
    """Serializer for feature flags"""
    created_by_name = serializers.SerializerMethodField()
    updated_by_name = serializers.SerializerMethodField()
    school_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FeatureFlag
        fields = [
            'id', 'name', 'display_name', 'description', 'is_enabled',
            'is_permanent', 'applies_to_schools', 'applies_to_roles',
            'created_at', 'updated_at', 'created_by', 'updated_by',
            'created_by_name', 'updated_by_name', 'school_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name()
        return None
    
    def get_updated_by_name(self, obj):
        if obj.updated_by:
            return obj.updated_by.get_full_name()
        return None
    
    def get_school_count(self, obj):
        return obj.applies_to_schools.count()


class ConfigChangeLogSerializer(serializers.ModelSerializer):
    """Serializer for configuration change logs"""
    changed_by_name = serializers.SerializerMethodField()
    config_name = serializers.SerializerMethodField()
    
    class Meta:
        model = ConfigChangeLog
        fields = [
            'id', 'config', 'config_name', 'old_value', 'new_value',
            'change_reason', 'changed_by', 'changed_by_name',
            'changed_at', 'ip_address'
        ]
        read_only_fields = ['id', 'changed_at']
    
    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return obj.changed_by.get_full_name()
        return None
    
    def get_config_name(self, obj):
        return obj.config.name


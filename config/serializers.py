"""
Serializers for system configuration models
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import SystemConfig, FeatureFlag, ConfigChangeLog

User = get_user_model()


class SystemConfigSerializer(serializers.ModelSerializer):
    """Serializer for SystemConfig model"""
    
    typed_value = serializers.SerializerMethodField()
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = SystemConfig
        fields = [
            'id', 'key', 'value', 'typed_value', 'config_type', 'name', 
            'description', 'category', 'is_public', 'is_editable',
            'validation_regex', 'min_value', 'max_value',
            'created_at', 'updated_at', 'updated_by', 'updated_by_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'updated_by', 'updated_by_name', 'typed_value']
    
    def get_typed_value(self, obj):
        """Get the properly typed value"""
        return obj.get_typed_value()
    
    def validate_key(self, value):
        """Validate configuration key format"""
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_\.]*$', value):
            raise serializers.ValidationError(
                "Key must start with a letter and contain only letters, numbers, underscores, and dots"
            )
        return value
    
    def validate(self, attrs):
        """Cross-field validation"""
        config_type = attrs.get('config_type')
        value = attrs.get('value', '')
        
        # Type-specific validation
        if config_type == 'INTEGER':
            try:
                int_val = int(value)
                min_val = attrs.get('min_value')
                max_val = attrs.get('max_value')
                if min_val is not None and int_val < min_val:
                    raise serializers.ValidationError({'value': f'Value must be at least {min_val}'})
                if max_val is not None and int_val > max_val:
                    raise serializers.ValidationError({'value': f'Value must be at most {max_val}'})
            except ValueError:
                raise serializers.ValidationError({'value': 'Value must be a valid integer'})
        
        elif config_type == 'FLOAT':
            try:
                float_val = float(value)
                min_val = attrs.get('min_value')
                max_val = attrs.get('max_value')
                if min_val is not None and float_val < min_val:
                    raise serializers.ValidationError({'value': f'Value must be at least {min_val}'})
                if max_val is not None and float_val > max_val:
                    raise serializers.ValidationError({'value': f'Value must be at most {max_val}'})
            except ValueError:
                raise serializers.ValidationError({'value': 'Value must be a valid number'})
        
        elif config_type == 'BOOLEAN':
            if value.lower() not in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off'):
                raise serializers.ValidationError({
                    'value': 'Boolean value must be true/false, 1/0, yes/no, or on/off'
                })
        
        elif config_type == 'JSON':
            try:
                import json
                json.loads(value)
            except json.JSONDecodeError:
                raise serializers.ValidationError({'value': 'Value must be valid JSON'})
        
        elif config_type == 'URL':
            from django.core.validators import URLValidator
            try:
                URLValidator()(value)
            except serializers.ValidationError:
                raise serializers.ValidationError({'value': 'Value must be a valid URL'})
        
        elif config_type == 'EMAIL':
            from django.core.validators import EmailValidator
            try:
                EmailValidator()(value)
            except serializers.ValidationError:
                raise serializers.ValidationError({'value': 'Value must be a valid email address'})
        
        elif config_type == 'COLOR':
            import re
            if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
                raise serializers.ValidationError({'value': 'Color must be in hex format (#RRGGBB)'})
        
        return attrs


class FeatureFlagSerializer(serializers.ModelSerializer):
    """Serializer for FeatureFlag model"""
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    school_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FeatureFlag
        fields = [
            'id', 'name', 'display_name', 'description', 'is_enabled', 'is_permanent',
            'applies_to_schools', 'applies_to_roles', 'school_count',
            'created_at', 'updated_at', 'created_by', 'created_by_name', 
            'updated_by', 'updated_by_name'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by', 'created_by_name',
            'updated_by', 'updated_by_name', 'school_count'
        ]
    
    def get_school_count(self, obj):
        """Get number of schools this flag applies to"""
        return obj.applies_to_schools.count()
    
    def validate_name(self, value):
        """Validate feature flag name format"""
        import re
        if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
            raise serializers.ValidationError(
                "Name must start with a letter and contain only letters, numbers, and underscores"
            )
        return value
    
    def validate_applies_to_roles(self, value):
        """Validate role choices"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Roles must be a list")
        
        valid_roles = [choice[0] for choice in User.Role.choices]
        for role in value:
            if role not in valid_roles:
                raise serializers.ValidationError(f"Invalid role: {role}")
        
        return value


class ConfigChangeLogSerializer(serializers.ModelSerializer):
    """Serializer for ConfigChangeLog model"""
    
    config_name = serializers.CharField(source='config.name', read_only=True)
    config_key = serializers.CharField(source='config.key', read_only=True)
    changed_by_name = serializers.CharField(source='changed_by.get_full_name', read_only=True)
    
    class Meta:
        model = ConfigChangeLog
        fields = [
            'id', 'config', 'config_name', 'config_key',
            'old_value', 'new_value', 'change_reason',
            'changed_by', 'changed_by_name', 'changed_at', 'ip_address'
        ]
        read_only_fields = ['id', 'changed_at', 'config_name', 'config_key', 'changed_by_name']


class PublicConfigSerializer(serializers.Serializer):
    """Serializer for public configuration response"""
    
    config = serializers.DictField()
    features = serializers.DictField()
    generated_at = serializers.DateTimeField()


class BulkConfigUpdateSerializer(serializers.Serializer):
    """Serializer for bulk configuration updates"""
    
    configs = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
            required=True
        ),
        min_length=1
    )
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    
    def validate_configs(self, value):
        """Validate each config update"""
        for config_data in value:
            if 'key' not in config_data:
                raise serializers.ValidationError("Each config must have a 'key' field")
            if 'value' not in config_data:
                raise serializers.ValidationError("Each config must have a 'value' field")
        return value


class FeatureFlagCheckSerializer(serializers.Serializer):
    """Serializer for feature flag checks"""
    
    flag_name = serializers.CharField(max_length=100)
    user_id = serializers.UUIDField(required=False)
    school_id = serializers.UUIDField(required=False)
    
    def validate_flag_name(self, value):
        """Check if feature flag exists"""
        if not FeatureFlag.objects.filter(name=value).exists():
            raise serializers.ValidationError(f"Feature flag '{value}' does not exist")
        return value

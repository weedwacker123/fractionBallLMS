"""
System configuration models for branding, feature flags, and settings
"""
from django.db import models
from django.core.validators import URLValidator
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class SystemConfig(models.Model):
    """
    Global system configuration settings
    """
    
    CONFIG_TYPES = [
        ('STRING', 'String'),
        ('INTEGER', 'Integer'),
        ('FLOAT', 'Float'),
        ('BOOLEAN', 'Boolean'),
        ('JSON', 'JSON'),
        ('URL', 'URL'),
        ('EMAIL', 'Email'),
        ('COLOR', 'Color'),
        ('FILE', 'File Path'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    key = models.CharField(
        max_length=100, 
        unique=True, 
        db_index=True,
        help_text="Unique configuration key (e.g., 'branding.logo_url')"
    )
    value = models.TextField(
        help_text="Configuration value (stored as text, converted based on config_type)"
    )
    config_type = models.CharField(
        max_length=20, 
        choices=CONFIG_TYPES, 
        default='STRING',
        help_text="Data type for proper value conversion"
    )
    
    # Metadata
    name = models.CharField(
        max_length=200,
        help_text="Human-readable name for admin interface"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this configuration controls"
    )
    category = models.CharField(
        max_length=50,
        default='general',
        help_text="Configuration category for organization"
    )
    
    # Access control
    is_public = models.BooleanField(
        default=False,
        help_text="Whether this config is accessible via public API"
    )
    is_editable = models.BooleanField(
        default=True,
        help_text="Whether this config can be edited via admin interface"
    )
    
    # Validation
    validation_regex = models.CharField(
        max_length=500,
        blank=True,
        help_text="Optional regex pattern for value validation"
    )
    min_value = models.FloatField(
        null=True, 
        blank=True,
        help_text="Minimum value for numeric types"
    )
    max_value = models.FloatField(
        null=True, 
        blank=True,
        help_text="Maximum value for numeric types"
    )
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='config_updates'
    )
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'System Configuration'
        verbose_name_plural = 'System Configurations'
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['category', 'name']),
            models.Index(fields=['is_public']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.key})"
    
    def get_typed_value(self):
        """Convert string value to appropriate type"""
        if not self.value:
            return None
        
        try:
            if self.config_type == 'BOOLEAN':
                return self.value.lower() in ('true', '1', 'yes', 'on')
            elif self.config_type == 'INTEGER':
                return int(self.value)
            elif self.config_type == 'FLOAT':
                return float(self.value)
            elif self.config_type == 'JSON':
                import json
                return json.loads(self.value)
            else:
                return self.value
        except (ValueError, TypeError, json.JSONDecodeError):
            return self.value  # Return as string if conversion fails
    
    def set_typed_value(self, value):
        """Set value with appropriate type conversion"""
        if value is None:
            self.value = ''
        elif self.config_type == 'JSON':
            import json
            self.value = json.dumps(value)
        else:
            self.value = str(value)
    
    def clean(self):
        """Validate configuration value"""
        from django.core.exceptions import ValidationError
        import re
        import json
        
        errors = {}
        
        # Type-specific validation
        try:
            if self.config_type == 'INTEGER':
                int_val = int(self.value)
                if self.min_value is not None and int_val < self.min_value:
                    errors['value'] = f'Value must be at least {self.min_value}'
                if self.max_value is not None and int_val > self.max_value:
                    errors['value'] = f'Value must be at most {self.max_value}'
            
            elif self.config_type == 'FLOAT':
                float_val = float(self.value)
                if self.min_value is not None and float_val < self.min_value:
                    errors['value'] = f'Value must be at least {self.min_value}'
                if self.max_value is not None and float_val > self.max_value:
                    errors['value'] = f'Value must be at most {self.max_value}'
            
            elif self.config_type == 'BOOLEAN':
                if self.value.lower() not in ('true', 'false', '1', '0', 'yes', 'no', 'on', 'off'):
                    errors['value'] = 'Boolean value must be true/false, 1/0, yes/no, or on/off'
            
            elif self.config_type == 'JSON':
                json.loads(self.value)
            
            elif self.config_type == 'URL':
                URLValidator()(self.value)
            
            elif self.config_type == 'EMAIL':
                from django.core.validators import EmailValidator
                EmailValidator()(self.value)
            
            elif self.config_type == 'COLOR':
                # Validate hex color format
                if not re.match(r'^#[0-9A-Fa-f]{6}$', self.value):
                    errors['value'] = 'Color must be in hex format (#RRGGBB)'
        
        except (ValueError, TypeError, json.JSONDecodeError) as e:
            errors['value'] = f'Invalid {self.config_type.lower()} format: {str(e)}'
        
        # Regex validation
        if self.validation_regex and self.value:
            try:
                if not re.match(self.validation_regex, self.value):
                    errors['value'] = f'Value does not match required pattern: {self.validation_regex}'
            except re.error:
                errors['validation_regex'] = 'Invalid regex pattern'
        
        if errors:
            raise ValidationError(errors)


class FeatureFlag(models.Model):
    """
    Feature flags for enabling/disabling functionality
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100, 
        unique=True, 
        db_index=True,
        help_text="Unique feature flag name (e.g., 'video_downloads_enabled')"
    )
    display_name = models.CharField(
        max_length=200,
        help_text="Human-readable feature name"
    )
    description = models.TextField(
        help_text="Description of what this feature flag controls"
    )
    
    # Flag settings
    is_enabled = models.BooleanField(
        default=False,
        help_text="Whether this feature is currently enabled"
    )
    is_permanent = models.BooleanField(
        default=False,
        help_text="Whether this flag can be toggled (false) or is permanent (true)"
    )
    
    # Scoping
    applies_to_schools = models.ManyToManyField(
        'accounts.School',
        blank=True,
        help_text="If specified, flag only applies to these schools"
    )
    applies_to_roles = models.JSONField(
        default=list,
        blank=True,
        help_text="If specified, flag only applies to these user roles"
    )
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='created_feature_flags'
    )
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='updated_feature_flags'
    )
    
    class Meta:
        ordering = ['display_name']
        verbose_name = 'Feature Flag'
        verbose_name_plural = 'Feature Flags'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_enabled']),
        ]
    
    def __str__(self):
        status = "✅" if self.is_enabled else "❌"
        return f"{status} {self.display_name}"
    
    def is_enabled_for_user(self, user):
        """Check if feature is enabled for specific user"""
        if not self.is_enabled:
            return False
        
        # Check school scoping
        if self.applies_to_schools.exists():
            if not user.school or user.school not in self.applies_to_schools.all():
                return False
        
        # Check role scoping
        if self.applies_to_roles:
            if user.role not in self.applies_to_roles:
                return False
        
        return True
    
    def is_enabled_for_school(self, school):
        """Check if feature is enabled for specific school"""
        if not self.is_enabled:
            return False
        
        if self.applies_to_schools.exists():
            return school in self.applies_to_schools.all()
        
        return True


class ConfigChangeLog(models.Model):
    """
    Audit log for configuration changes
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    config = models.ForeignKey(SystemConfig, on_delete=models.CASCADE, related_name='change_logs')
    
    # Change details
    old_value = models.TextField(blank=True)
    new_value = models.TextField()
    change_reason = models.TextField(blank=True)
    
    # Audit info
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        ordering = ['-changed_at']
        verbose_name = 'Configuration Change Log'
        verbose_name_plural = 'Configuration Change Logs'
        indexes = [
            models.Index(fields=['config', 'changed_at']),
            models.Index(fields=['changed_by', 'changed_at']),
        ]
    
    def __str__(self):
        return f"{self.config.name} changed by {self.changed_by} at {self.changed_at}"

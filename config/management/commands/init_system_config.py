from django.core.management.base import BaseCommand
from django.db import transaction
from config.models import SystemConfig, FeatureFlag
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Initialize default system configuration and feature flags'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset existing configurations to defaults',
        )

    def handle(self, *args, **options):
        reset_configs = options['reset']
        
        self.stdout.write('🔧 Initializing system configuration...')
        
        with transaction.atomic():
            # Initialize default configurations
            self.create_default_configs(reset_configs)
            
            # Initialize default feature flags
            self.create_default_feature_flags(reset_configs)
        
        self.stdout.write(
            self.style.SUCCESS('✅ System configuration initialized successfully!')
        )

    def create_default_configs(self, reset=False):
        """Create default system configurations"""
        
        default_configs = [
            # Branding configurations
            {
                'key': 'branding.site_name',
                'value': 'Fraction Ball LMS',
                'config_type': 'STRING',
                'name': 'Site Name',
                'description': 'The name of the platform displayed in headers and titles',
                'category': 'branding',
                'is_public': True,
                'is_editable': True
            },
            {
                'key': 'branding.logo_url',
                'value': '',
                'config_type': 'URL',
                'name': 'Logo URL',
                'description': 'URL to the platform logo image',
                'category': 'branding',
                'is_public': True,
                'is_editable': True
            },
            {
                'key': 'branding.primary_color',
                'value': '#3B82F6',
                'config_type': 'COLOR',
                'name': 'Primary Color',
                'description': 'Primary brand color used throughout the interface',
                'category': 'branding',
                'is_public': True,
                'is_editable': True
            },
            {
                'key': 'branding.secondary_color',
                'value': '#6B7280',
                'config_type': 'COLOR',
                'name': 'Secondary Color',
                'description': 'Secondary brand color for accents and highlights',
                'category': 'branding',
                'is_public': True,
                'is_editable': True
            },
            
            # Legal and compliance
            {
                'key': 'legal.privacy_policy_url',
                'value': '/privacy',
                'config_type': 'STRING',
                'name': 'Privacy Policy URL',
                'description': 'Link to the privacy policy page',
                'category': 'legal',
                'is_public': True,
                'is_editable': True
            },
            {
                'key': 'legal.terms_of_service_url',
                'value': '/terms',
                'config_type': 'STRING',
                'name': 'Terms of Service URL',
                'description': 'Link to the terms of service page',
                'category': 'legal',
                'is_public': True,
                'is_editable': True
            },
            {
                'key': 'legal.support_email',
                'value': 'support@fractionball.edu',
                'config_type': 'EMAIL',
                'name': 'Support Email',
                'description': 'Email address for user support and inquiries',
                'category': 'legal',
                'is_public': True,
                'is_editable': True
            },
            
            # System settings
            {
                'key': 'system.max_upload_size_mb',
                'value': '500',
                'config_type': 'INTEGER',
                'name': 'Maximum Upload Size (MB)',
                'description': 'Maximum file size allowed for uploads in megabytes',
                'category': 'system',
                'is_public': False,
                'is_editable': True,
                'min_value': 1,
                'max_value': 2000
            },
            {
                'key': 'system.session_timeout_minutes',
                'value': '480',
                'config_type': 'INTEGER',
                'name': 'Session Timeout (minutes)',
                'description': 'User session timeout in minutes',
                'category': 'system',
                'is_public': False,
                'is_editable': True,
                'min_value': 30,
                'max_value': 1440
            },
            {
                'key': 'system.maintenance_mode',
                'value': 'false',
                'config_type': 'BOOLEAN',
                'name': 'Maintenance Mode',
                'description': 'Enable maintenance mode to restrict access',
                'category': 'system',
                'is_public': True,
                'is_editable': True
            },
            
            # Content settings
            {
                'key': 'content.auto_approval_enabled',
                'value': 'false',
                'config_type': 'BOOLEAN',
                'name': 'Auto-approval Enabled',
                'description': 'Automatically approve content from trusted users',
                'category': 'content',
                'is_public': False,
                'is_editable': True
            },
            {
                'key': 'content.default_video_quality',
                'value': '720p',
                'config_type': 'STRING',
                'name': 'Default Video Quality',
                'description': 'Default video quality setting for playback',
                'category': 'content',
                'is_public': True,
                'is_editable': True
            },
            
            # Analytics settings
            {
                'key': 'analytics.tracking_enabled',
                'value': 'true',
                'config_type': 'BOOLEAN',
                'name': 'Analytics Tracking Enabled',
                'description': 'Enable user activity tracking and analytics',
                'category': 'analytics',
                'is_public': False,
                'is_editable': True
            },
            {
                'key': 'analytics.retention_days',
                'value': '365',
                'config_type': 'INTEGER',
                'name': 'Data Retention (days)',
                'description': 'Number of days to retain analytics data',
                'category': 'analytics',
                'is_public': False,
                'is_editable': True,
                'min_value': 30,
                'max_value': 2555  # ~7 years
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for config_data in default_configs:
            config, created = SystemConfig.objects.get_or_create(
                key=config_data['key'],
                defaults=config_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ Created config: {config.name}')
            elif reset:
                # Update existing config with new defaults
                for field, value in config_data.items():
                    if field != 'key':
                        setattr(config, field, value)
                config.save()
                updated_count += 1
                self.stdout.write(f'  🔄 Updated config: {config.name}')
        
        self.stdout.write(f'📊 Configurations: {created_count} created, {updated_count} updated')

    def create_default_feature_flags(self, reset=False):
        """Create default feature flags"""
        
        default_flags = [
            {
                'name': 'video_downloads_disabled',
                'display_name': 'Video Downloads Disabled',
                'description': 'Disable direct video downloads (streaming only policy)',
                'is_enabled': True,
                'is_permanent': True,  # Cannot be toggled - policy enforcement
                'applies_to_roles': []
            },
            {
                'name': 'bulk_upload_enabled',
                'display_name': 'Bulk Upload Enabled',
                'description': 'Allow CSV bulk upload of content',
                'is_enabled': True,
                'is_permanent': False,
                'applies_to_roles': ['TEACHER', 'SCHOOL_ADMIN', 'ADMIN']
            },
            {
                'name': 'advanced_analytics_enabled',
                'display_name': 'Advanced Analytics Enabled',
                'description': 'Enable advanced analytics and reporting features',
                'is_enabled': True,
                'is_permanent': False,
                'applies_to_roles': ['SCHOOL_ADMIN', 'ADMIN']
            },
            {
                'name': 'playlist_sharing_enabled',
                'display_name': 'Playlist Sharing Enabled',
                'description': 'Allow teachers to share playlists with other teachers',
                'is_enabled': True,
                'is_permanent': False,
                'applies_to_roles': ['TEACHER', 'SCHOOL_ADMIN', 'ADMIN']
            },
            {
                'name': 'content_approval_required',
                'display_name': 'Content Approval Required',
                'description': 'Require admin approval before content is published',
                'is_enabled': True,
                'is_permanent': False,
                'applies_to_roles': []
            },
            {
                'name': 'user_registration_enabled',
                'display_name': 'User Registration Enabled',
                'description': 'Allow new user registration (when disabled, admin-only creation)',
                'is_enabled': False,
                'is_permanent': False,
                'applies_to_roles': []
            },
            {
                'name': 'api_rate_limiting_enabled',
                'display_name': 'API Rate Limiting Enabled',
                'description': 'Enable rate limiting on API endpoints',
                'is_enabled': True,
                'is_permanent': False,
                'applies_to_roles': []
            },
            {
                'name': 'external_integrations_enabled',
                'display_name': 'External Integrations Enabled',
                'description': 'Allow integration with external services and APIs',
                'is_enabled': True,
                'is_permanent': False,
                'applies_to_roles': ['ADMIN']
            }
        ]
        
        created_count = 0
        updated_count = 0
        
        for flag_data in default_flags:
            flag, created = FeatureFlag.objects.get_or_create(
                name=flag_data['name'],
                defaults=flag_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  🚩 Created feature flag: {flag.display_name}')
            elif reset and not flag.is_permanent:
                # Update non-permanent flags
                for field, value in flag_data.items():
                    if field not in ['name', 'is_permanent']:
                        setattr(flag, field, value)
                flag.save()
                updated_count += 1
                self.stdout.write(f'  🔄 Updated feature flag: {flag.display_name}')
        
        self.stdout.write(f'🚩 Feature flags: {created_count} created, {updated_count} updated')

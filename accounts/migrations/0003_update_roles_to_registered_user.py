# Generated migration for updating user roles to four-tier system

from django.db import migrations, models


def migrate_roles_forward(apps, schema_editor):
    """
    Migrate existing users to new role system:
    - ADMIN stays ADMIN
    - CONTENT_MANAGER stays CONTENT_MANAGER
    - SCHOOL_ADMIN -> REGISTERED_USER
    - TEACHER -> REGISTERED_USER
    """
    User = apps.get_model('accounts', 'User')
    # Update SCHOOL_ADMIN and TEACHER to REGISTERED_USER
    User.objects.filter(role__in=['SCHOOL_ADMIN', 'TEACHER']).update(role='REGISTERED_USER')


def migrate_roles_backward(apps, schema_editor):
    """
    Rollback: convert REGISTERED_USER back to TEACHER
    """
    User = apps.get_model('accounts', 'User')
    User.objects.filter(role='REGISTERED_USER').update(role='TEACHER')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_add_content_manager_role'),
    ]

    operations = [
        # First, run the data migration to update existing user roles
        migrations.RunPython(migrate_roles_forward, migrate_roles_backward),

        # Then, alter the field to update choices and default
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('ADMIN', 'Site Administrator'),
                    ('CONTENT_MANAGER', 'Content Manager'),
                    ('REGISTERED_USER', 'Registered User'),
                ],
                default='REGISTERED_USER',
                help_text='User role determines access permissions',
                max_length=20,
            ),
        ),
    ]

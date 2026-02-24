"""
Management command to seed Firestore with default role definitions.
Creates ADMIN, CONTENT_MANAGER, and REGISTERED_USER roles that match
the original hardcoded behavior.
"""
from datetime import datetime
from django.core.management.base import BaseCommand
from content.firestore_service import get_firestore_client
from accounts.role_service import PERMISSION_KEYS


SEED_ROLES = [
    {
        'key': 'ADMIN',
        'name': 'Site Administrator',
        'description': 'Full system access including user and school management.',
        'isSystem': True,
        'displayOrder': 1,
        'permissions': {k: True for k in PERMISSION_KEYS},
    },
    {
        'key': 'CONTENT_MANAGER',
        'name': 'Content Manager',
        'description': 'Can manage content, moderate community, and access CMS.',
        'isSystem': True,
        'displayOrder': 2,
        'permissions': {
            'cms_view': True,
            'cms_edit': True,
            'activities_view': True,
            'resources_download': True,
            'community_post': True,
            'community_moderate': True,
        },
    },
    {
        'key': 'REGISTERED_USER',
        'name': 'Registered User',
        'description': 'Basic authenticated user with access to activities, resources, and community.',
        'isSystem': True,
        'displayOrder': 3,
        'permissions': {
            'cms_view': False,
            'cms_edit': False,
            'activities_view': True,
            'resources_download': True,
            'community_post': True,
            'community_moderate': False,
        },
    },
    {
        'key': 'GUEST',
        'name': 'Guest Viewer',
        'description': 'Unauthenticated visitor with read-only access to public content.',
        'isSystem': True,
        'displayOrder': 4,
        'permissions': {k: False for k in PERMISSION_KEYS},
    },
]


class Command(BaseCommand):
    help = 'Seed Firestore roles collection with default role definitions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Overwrite existing role documents',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        force = options.get('force', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - no changes will be made'))

        db = get_firestore_client()
        now = datetime.utcnow()

        for role_data in SEED_ROLES:
            doc_id = role_data['key']
            doc_ref = db.collection('roles').document(doc_id)
            existing = doc_ref.get()

            if existing.exists and not force:
                self.stdout.write(
                    self.style.WARNING(f"  SKIP: {doc_id} already exists (use --force to overwrite)")
                )
                continue

            doc = {
                **role_data,
                'createdAt': now,
                'updatedAt': now,
            }

            if dry_run:
                self.stdout.write(self.style.SUCCESS(
                    f"  WOULD CREATE: {doc_id} ({role_data['name']})"
                ))
                perms_true = [k for k, v in role_data['permissions'].items() if v]
                self.stdout.write(f"    Permissions: {', '.join(perms_true)}")
            else:
                doc_ref.set(doc)
                self.stdout.write(self.style.SUCCESS(
                    f"  CREATED: {doc_id} ({role_data['name']})"
                ))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\nRoles seeded successfully.'))
            self.stdout.write('Run "python manage.py seed_roles --dry-run" to preview changes.')

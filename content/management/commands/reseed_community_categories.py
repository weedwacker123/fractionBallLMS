"""
Management command to fix community post categories in Firestore.
Maps any invalid/old category values to the 4 valid Firestore categories:
  question, discussion, resource_share, announcement
"""
from django.core.management.base import BaseCommand
from content.firestore_service import get_firestore_client


# Valid Firestore categories
VALID_CATEGORIES = {'question', 'discussion', 'resource_share', 'announcement'}

# Map old ORM categories (and common variants) to valid Firestore categories
CATEGORY_MAP = {
    # Old ORM category names/slugs → Firestore categories
    'General Discussion': 'discussion',
    'general': 'discussion',
    'Activity Tips & Strategies': 'discussion',
    'activity-tips': 'discussion',
    'Questions & Help': 'question',
    'questions': 'question',
    'Success Stories': 'discussion',
    'success-stories': 'discussion',
    'Adaptations & Modifications': 'resource_share',
    'adaptations': 'resource_share',
    'Resource Requests': 'resource_share',
    'resources': 'resource_share',
}


class Command(BaseCommand):
    help = 'Fix community post categories in Firestore to use valid enum values'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without writing to Firestore',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be written\n'))

        db = get_firestore_client()
        docs = list(db.collection('communityPosts').stream())

        self.stdout.write(f'Found {len(docs)} community posts in Firestore\n')

        updated = 0
        already_valid = 0
        empty_set = 0

        for doc in docs:
            data = doc.to_dict()
            category = data.get('category', '')
            title = data.get('title', '(untitled)')[:50]

            if category in VALID_CATEGORIES:
                already_valid += 1
                continue

            # Try to map the old category
            new_category = CATEGORY_MAP.get(category)
            if not new_category:
                # Fallback: assign 'discussion' for any unrecognized value
                new_category = 'discussion'

            if not category:
                label = '(empty)'
            else:
                label = category

            self.stdout.write(
                f'  {title} — "{label}" -> "{new_category}"'
            )

            if not dry_run:
                doc.reference.update({'category': new_category})
                updated += 1
            else:
                empty_set += 1

        self.stdout.write('')
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'Would update {empty_set + updated} posts. '
                f'{already_valid} already valid.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Updated {updated} posts. {already_valid} already valid.'
            ))

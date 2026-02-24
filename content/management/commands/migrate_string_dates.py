"""
One-time migration: convert ISO string dates to Firestore Timestamps.

Django views previously wrote dates as .isoformat() strings. FireCMS expects
native Firestore Timestamps (dataType: "date"). This command finds all string
date fields and converts them to datetime objects, which the Firestore SDK
stores as Timestamps.

Usage:
    python manage.py migrate_string_dates          # dry run
    python manage.py migrate_string_dates --apply  # apply changes
"""
from django.core.management.base import BaseCommand
from datetime import datetime, timezone


# Collections and their date fields to migrate
COLLECTIONS_DATE_FIELDS = {
    'activities': ['createdAt', 'updatedAt'],
    'menuItems': ['createdAt', 'updatedAt'],
    'faqs': ['createdAt', 'updatedAt'],
    'communityPosts': ['createdAt', 'updatedAt', 'flaggedAt', 'moderatedAt'],
    'users': ['createdAt', 'updatedAt', 'lastLogin'],
    'taxonomies': ['createdAt', 'updatedAt'],
    'siteConfig': ['updatedAt'],
}

# Subcollections: parent_collection -> { subcollection_name: [date_fields] }
SUBCOLLECTIONS_DATE_FIELDS = {
    'communityPosts': {
        'comments': ['createdAt', 'updatedAt'],
    },
}


def get_firestore_client():
    from google.cloud import firestore as gc_firestore
    from google.oauth2 import service_account
    from django.conf import settings

    credentials = service_account.Credentials.from_service_account_info(
        settings.FIREBASE_CONFIG
    )
    return gc_firestore.Client(
        project='fractionball-lms',
        database='default',
        credentials=credentials
    )


def parse_iso_string(value):
    """Parse an ISO 8601 string to a timezone-aware datetime."""
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


class Command(BaseCommand):
    help = 'Convert ISO string dates to Firestore Timestamps in all collections'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Actually apply changes (default is dry run)',
        )

    def handle(self, *args, **options):
        apply = options['apply']
        db = get_firestore_client()

        if not apply:
            self.stdout.write(self.style.WARNING('DRY RUN — no changes will be made. Use --apply to write.\n'))

        total_fixed = 0

        for collection_name, date_fields in COLLECTIONS_DATE_FIELDS.items():
            fixed = self._migrate_collection(db, collection_name, date_fields, apply)
            total_fixed += fixed

            # Handle subcollections
            if collection_name in SUBCOLLECTIONS_DATE_FIELDS:
                for sub_name, sub_fields in SUBCOLLECTIONS_DATE_FIELDS[collection_name].items():
                    fixed = self._migrate_subcollections(
                        db, collection_name, sub_name, sub_fields, apply
                    )
                    total_fixed += fixed

        if apply:
            self.stdout.write(self.style.SUCCESS(f'\nDone. Fixed {total_fixed} documents.'))
        else:
            self.stdout.write(self.style.WARNING(f'\nDry run complete. {total_fixed} documents would be fixed. Run with --apply to write.'))

    def _migrate_collection(self, db, collection_name, date_fields, apply):
        docs = db.collection(collection_name).stream()
        fixed = 0

        for doc in docs:
            data = doc.to_dict()
            updates = {}

            for field in date_fields:
                value = data.get(field)
                parsed = parse_iso_string(value)
                if parsed is not None:
                    updates[field] = parsed

            if updates:
                fixed += 1
                fields_str = ', '.join(f'{k}' for k in updates)
                self.stdout.write(f'  {collection_name}/{doc.id}: {fields_str}')
                if apply:
                    doc.reference.update(updates)

        if fixed:
            self.stdout.write(self.style.SUCCESS(f'  [{collection_name}] {fixed} docs with string dates'))
        else:
            self.stdout.write(f'  [{collection_name}] all dates OK')

        return fixed

    def _migrate_subcollections(self, db, parent_collection, sub_name, date_fields, apply):
        parent_docs = db.collection(parent_collection).stream()
        fixed = 0

        for parent_doc in parent_docs:
            sub_docs = parent_doc.reference.collection(sub_name).stream()
            for doc in sub_docs:
                data = doc.to_dict()
                updates = {}

                for field in date_fields:
                    value = data.get(field)
                    parsed = parse_iso_string(value)
                    if parsed is not None:
                        updates[field] = parsed

                if updates:
                    fixed += 1
                    fields_str = ', '.join(f'{k}' for k in updates)
                    self.stdout.write(f'  {parent_collection}/{parent_doc.id}/{sub_name}/{doc.id}: {fields_str}')
                    if apply:
                        doc.reference.update(updates)

        if fixed:
            self.stdout.write(self.style.SUCCESS(f'  [{parent_collection}/{sub_name}] {fixed} docs with string dates'))
        else:
            self.stdout.write(f'  [{parent_collection}/{sub_name}] all dates OK')

        return fixed

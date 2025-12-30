"""
Django management command to sync Firestore content to Django database

Usage:
    python manage.py sync_firestore                    # Sync all content
    python manage.py sync_firestore --collection=videos  # Sync only videos
    python manage.py sync_firestore --dry-run          # Show what would be synced
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from accounts.models import School
from content.firestore_service import (
    full_sync, 
    sync_videos_to_django, 
    sync_resources_to_django,
    sync_activities_to_django,
    get_videos,
    get_resources,
    get_published_activities
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Sync content from Firestore (FireCMS) to Django database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--collection',
            type=str,
            choices=['videos', 'resources', 'activities', 'all'],
            default='all',
            help='Which collection to sync (default: all)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes'
        )
        parser.add_argument(
            '--user-email',
            type=str,
            help='Email of user to use as owner (defaults to first admin)'
        )
        parser.add_argument(
            '--school-name',
            type=str,
            help='Name of school to associate content with (defaults to first school)'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🔄 Starting Firestore → Django sync...'))
        
        # Get user
        user_email = options.get('user_email')
        if user_email:
            user = User.objects.filter(email=user_email).first()
            if not user:
                raise CommandError(f'User with email "{user_email}" not found')
        else:
            user = User.objects.filter(is_admin=True).first() or User.objects.first()
            if not user:
                raise CommandError('No users found. Please create a user first.')
        
        self.stdout.write(f'📧 Using user: {user.email}')
        
        # Get school
        school_name = options.get('school_name')
        if school_name:
            school = School.objects.filter(name__icontains=school_name).first()
            if not school:
                raise CommandError(f'School "{school_name}" not found')
        else:
            school = School.objects.first()
            if not school:
                # Create a default school if none exists
                school = School.objects.create(
                    name='Fraction Ball School',
                    district_name='Default District'
                )
                self.stdout.write(self.style.WARNING('⚠️ Created default school: Fraction Ball School'))
        
        self.stdout.write(f'🏫 Using school: {school.name}')
        
        collection = options['collection']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN - No changes will be made'))
            self._dry_run(collection)
            return
        
        # Perform sync
        try:
            if collection == 'all':
                results = full_sync(user, school)
                self._print_results(results)
            elif collection == 'videos':
                created, updated = sync_videos_to_django(user, school)
                self._print_single_result('Videos', created, updated)
            elif collection == 'resources':
                created, updated = sync_resources_to_django(user, school)
                self._print_single_result('Resources', created, updated)
            elif collection == 'activities':
                created, updated = sync_activities_to_django(user, school)
                self._print_single_result('Activities', created, updated)
            
            self.stdout.write(self.style.SUCCESS('✅ Sync completed successfully!'))
            
        except Exception as e:
            raise CommandError(f'Sync failed: {e}')

    def _dry_run(self, collection):
        """Show what would be synced without making changes"""
        
        if collection in ['all', 'videos']:
            videos = get_videos()
            self.stdout.write(f'\n📹 Videos to sync: {len(videos)}')
            for v in videos[:5]:  # Show first 5
                self.stdout.write(f'   - {v.get("title", "Untitled")}')
            if len(videos) > 5:
                self.stdout.write(f'   ... and {len(videos) - 5} more')
        
        if collection in ['all', 'resources']:
            resources = get_resources()
            self.stdout.write(f'\n📄 Resources to sync: {len(resources)}')
            for r in resources[:5]:
                self.stdout.write(f'   - {r.get("title", "Untitled")}')
            if len(resources) > 5:
                self.stdout.write(f'   ... and {len(resources) - 5} more')
        
        if collection in ['all', 'activities']:
            activities = get_published_activities()
            self.stdout.write(f'\n🎯 Activities to sync: {len(activities)}')
            for a in activities[:5]:
                self.stdout.write(f'   - {a.get("title", "Untitled")}')
            if len(activities) > 5:
                self.stdout.write(f'   ... and {len(activities) - 5} more')

    def _print_results(self, results):
        """Print sync results summary"""
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('📊 Sync Results:'))
        self.stdout.write('=' * 50)
        
        for collection, counts in results.items():
            created = counts.get('created', 0)
            updated = counts.get('updated', 0)
            emoji = '📹' if collection == 'videos' else '📄' if collection == 'resources' else '🎯'
            self.stdout.write(f'{emoji} {collection.capitalize()}: {created} created, {updated} updated')
        
        self.stdout.write('=' * 50)

    def _print_single_result(self, name, created, updated):
        """Print single collection sync result"""
        self.stdout.write(f'\n📊 {name}: {created} created, {updated} updated')



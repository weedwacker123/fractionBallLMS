"""
Management command to seed forum categories
"""
from django.core.management.base import BaseCommand
from content.models import ForumCategory


class Command(BaseCommand):
    help = 'Seed initial forum categories'
    
    def handle(self, *args, **options):
        self.stdout.write('Seeding forum categories...')
        
        categories = [
            {
                'name': 'General Discussion',
                'slug': 'general',
                'description': 'General discussions about Fraction Ball and teaching fractions',
                'icon': 'chat',
                'color': 'blue',
                'order': 1,
            },
            {
                'name': 'Activity Tips & Strategies',
                'slug': 'activity-tips',
                'description': 'Share tips, strategies, and best practices for activities',
                'icon': 'lightbulb',
                'color': 'yellow',
                'order': 2,
            },
            {
                'name': 'Questions & Help',
                'slug': 'questions',
                'description': 'Ask questions and get help from the community',
                'icon': 'question',
                'color': 'red',
                'order': 3,
            },
            {
                'name': 'Success Stories',
                'slug': 'success-stories',
                'description': 'Share your success stories and student achievements',
                'icon': 'star',
                'color': 'green',
                'order': 4,
            },
            {
                'name': 'Adaptations & Modifications',
                'slug': 'adaptations',
                'description': 'Discuss how to adapt activities for different grade levels and abilities',
                'icon': 'adjust',
                'color': 'purple',
                'order': 5,
            },
            {
                'name': 'Resource Requests',
                'slug': 'resources',
                'description': 'Request or share additional resources and materials',
                'icon': 'document',
                'color': 'indigo',
                'order': 6,
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for cat_data in categories:
            category, created = ForumCategory.objects.update_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {category.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {category.name}')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_count} new categories and updated {updated_count} existing categories!'
            )
        )


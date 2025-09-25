from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from content.models import VideoAsset, Resource, Playlist, PlaylistItem, GRADE_CHOICES, TOPIC_CHOICES
from accounts.models import School
import random
from datetime import datetime, timedelta
from django.utils import timezone

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with canonical taxonomy and sample content'

    def add_arguments(self, parser):
        parser.add_argument(
            '--videos',
            type=int,
            default=50,
            help='Number of sample videos to create'
        )
        parser.add_argument(
            '--resources',
            type=int,
            default=20,
            help='Number of sample resources to create'
        )
        parser.add_argument(
            '--playlists',
            type=int,
            default=10,
            help='Number of sample playlists to create'
        )

    def handle(self, *args, **options):
        videos_count = options['videos']
        resources_count = options['resources']
        playlists_count = options['playlists']

        self.stdout.write('🌱 Seeding taxonomy and sample content...')

        # Get existing data
        schools = list(School.objects.all())
        teachers = list(User.objects.filter(role__in=['TEACHER', 'SCHOOL_ADMIN']))

        if not schools:
            self.stdout.write(self.style.ERROR('No schools found. Run seed_data first.'))
            return

        if not teachers:
            self.stdout.write(self.style.ERROR('No teachers found. Run seed_data first.'))
            return

        # Sample video titles by topic
        video_titles_by_topic = {
            'fractions_basics': [
                'Introduction to Fractions',
                'What is a Fraction?',
                'Parts of a Whole',
                'Fraction Vocabulary',
                'Understanding Numerators and Denominators'
            ],
            'equivalent_fractions': [
                'Finding Equivalent Fractions',
                'Simplifying Fractions',
                'Common Denominators',
                'Fraction Strips and Equivalents',
                'Visual Models for Equivalent Fractions'
            ],
            'comparing_ordering': [
                'Comparing Fractions with Same Denominators',
                'Comparing Fractions with Different Denominators',
                'Ordering Fractions from Least to Greatest',
                'Using Benchmark Fractions',
                'Greater Than, Less Than, or Equal'
            ],
            'number_line': [
                'Fractions on a Number Line',
                'Placing Fractions Between Whole Numbers',
                'Number Line Strategies',
                'Estimating Fraction Positions',
                'Number Line Games and Activities'
            ],
            'mixed_improper': [
                'Mixed Numbers vs Improper Fractions',
                'Converting Mixed to Improper',
                'Converting Improper to Mixed',
                'When to Use Each Form',
                'Real-World Mixed Number Examples'
            ],
            'add_subtract_fractions': [
                'Adding Fractions with Same Denominators',
                'Subtracting Fractions with Same Denominators',
                'Adding Fractions with Different Denominators',
                'Subtracting Fractions with Different Denominators',
                'Adding and Subtracting Mixed Numbers'
            ],
            'multiply_divide_fractions': [
                'Multiplying Fractions by Whole Numbers',
                'Multiplying Two Fractions',
                'Dividing Fractions',
                'Reciprocals and Division',
                'Real-World Multiplication and Division'
            ],
            'decimals_percents': [
                'Fractions to Decimals',
                'Decimals to Fractions',
                'Introduction to Percentages',
                'Fractions, Decimals, and Percents',
                'Converting Between Forms'
            ],
            'ratio_proportion': [
                'Introduction to Ratios',
                'Understanding Proportions',
                'Solving Proportions',
                'Scale Drawings and Maps',
                'Real-World Ratio Problems'
            ],
            'word_problems': [
                'Fraction Word Problem Strategies',
                'Identifying Key Information',
                'Drawing Pictures for Word Problems',
                'Multi-Step Fraction Problems',
                'Real-World Applications'
            ]
        }

        # Sample descriptions
        descriptions = [
            'This video introduces key concepts with clear examples and visual aids.',
            'Step-by-step explanation with practice problems included.',
            'Interactive lesson with real-world applications and examples.',
            'Comprehensive overview with multiple solution strategies.',
            'Engaging presentation with visual models and manipulatives.',
            'Detailed walkthrough with common mistakes and how to avoid them.',
            'Fun and interactive approach to learning this important concept.',
            'Clear explanations with plenty of practice opportunities.'
        ]

        # Sample tags
        all_tags = [
            'visual', 'interactive', 'beginner', 'intermediate', 'advanced',
            'problem-solving', 'real-world', 'hands-on', 'conceptual',
            'procedural', 'games', 'activities', 'assessment', 'review'
        ]

        # Create sample videos
        self.stdout.write(f'Creating {videos_count} sample videos...')
        videos_created = 0
        
        for i in range(videos_count):
            # Random grade and topic
            grade = random.choice([choice[0] for choice in GRADE_CHOICES])
            topic = random.choice([choice[0] for choice in TOPIC_CHOICES])
            
            # Get appropriate title for topic
            topic_titles = video_titles_by_topic.get(topic, ['Sample Video'])
            title = random.choice(topic_titles)
            if videos_created > 0 and random.random() < 0.3:  # Add variation
                title += f" - Part {random.randint(1, 3)}"
            
            # Random teacher and school
            teacher = random.choice(teachers)
            
            # Create video
            video = VideoAsset.objects.create(
                title=title,
                description=random.choice(descriptions),
                grade=grade,
                topic=topic,
                tags=random.sample(all_tags, random.randint(2, 5)),
                duration=random.randint(180, 1800),  # 3-30 minutes
                file_size=random.randint(50000000, 500000000),  # 50MB-500MB
                storage_uri=f'https://firebasestorage.googleapis.com/v0/b/project/o/videos%2F{i+1:04d}.mp4',
                thumbnail_uri=f'https://firebasestorage.googleapis.com/v0/b/project/o/thumbnails%2F{i+1:04d}.jpg',
                owner=teacher,
                school=teacher.school,
                status=random.choice(['DRAFT', 'PUBLISHED', 'PUBLISHED', 'PUBLISHED']),  # More published
                created_at=timezone.now() - timedelta(days=random.randint(1, 365))
            )
            videos_created += 1

        self.stdout.write(f'✅ Created {videos_created} sample videos')

        # Create sample resources
        self.stdout.write(f'Creating {resources_count} sample resources...')
        resource_titles = [
            'Fraction Worksheet - Basic Practice',
            'Equivalent Fractions Activity Sheet',
            'Fraction Number Line Template',
            'Mixed Numbers Practice Problems',
            'Fraction Games and Activities Guide',
            'Assessment Rubric for Fractions',
            'Parent Guide to Fractions',
            'Fraction Vocabulary Cards',
            'Real-World Fraction Problems',
            'Fraction Art Project Instructions'
        ]
        
        resource_types = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xlsx']
        
        resources_created = 0
        for i in range(resources_count):
            teacher = random.choice(teachers)
            file_type = random.choice(resource_types)
            
            resource = Resource.objects.create(
                title=random.choice(resource_titles),
                description=f'Helpful resource for teaching fractions to {random.choice([choice[1] for choice in GRADE_CHOICES])} students.',
                file_uri=f'https://firebasestorage.googleapis.com/v0/b/project/o/resources%2F{i+1:04d}.{file_type}',
                file_type=file_type,
                file_size=random.randint(100000, 10000000),  # 100KB-10MB
                grade=random.choice([choice[0] for choice in GRADE_CHOICES]) if random.random() < 0.7 else '',
                topic=random.choice([choice[0] for choice in TOPIC_CHOICES]) if random.random() < 0.7 else '',
                tags=random.sample(all_tags, random.randint(1, 3)),
                owner=teacher,
                school=teacher.school,
                status=random.choice(['DRAFT', 'PUBLISHED', 'PUBLISHED']),
                created_at=timezone.now() - timedelta(days=random.randint(1, 180))
            )
            resources_created += 1

        self.stdout.write(f'✅ Created {resources_created} sample resources')

        # Create sample playlists
        self.stdout.write(f'Creating {playlists_count} sample playlists...')
        playlist_names = [
            'Introduction to Fractions Unit',
            'Equivalent Fractions Lessons',
            'Fraction Operations Complete Course',
            'Visual Fraction Models',
            'Real-World Fraction Applications',
            'Assessment and Review Videos',
            'Advanced Fraction Concepts',
            'Fraction Games and Activities',
            'Parent Resources for Fractions',
            'Differentiated Fraction Instruction'
        ]
        
        playlists_created = 0
        for i in range(playlists_count):
            teacher = random.choice(teachers)
            
            # Get videos from the same school for the playlist
            school_videos = VideoAsset.objects.filter(
                school=teacher.school,
                status='PUBLISHED'
            ).order_by('?')[:random.randint(3, 8)]
            
            if school_videos.exists():
                playlist = Playlist.objects.create(
                    name=random.choice(playlist_names),
                    description=f'Curated collection of videos for effective fraction instruction.',
                    owner=teacher,
                    school=teacher.school,
                    is_public=random.choice([True, False]),
                    created_at=timezone.now() - timedelta(days=random.randint(1, 90))
                )
                
                # Add videos to playlist
                for order, video in enumerate(school_videos, 1):
                    PlaylistItem.objects.create(
                        playlist=playlist,
                        video_asset=video,
                        order=order,
                        notes=f'Video {order} in the sequence' if random.random() < 0.3 else ''
                    )
                
                playlists_created += 1

        self.stdout.write(f'✅ Created {playlists_created} sample playlists')

        # Summary
        total_videos = VideoAsset.objects.count()
        total_resources = Resource.objects.count()
        total_playlists = Playlist.objects.count()
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Taxonomy seeding completed!\n\n'
                f'📊 Summary:\n'
                f'   • Grades: {len(GRADE_CHOICES)} (K-8)\n'
                f'   • Topics: {len(TOPIC_CHOICES)} fraction concepts\n'
                f'   • Videos: {total_videos} total\n'
                f'   • Resources: {total_resources} total\n'
                f'   • Playlists: {total_playlists} total\n\n'
                f'🏫 Content is distributed across {len(schools)} schools\n'
                f'👩‍🏫 Created by {len(teachers)} teachers\n\n'
                f'✨ Ready to test the content management system!'
            )
        )

        # Display taxonomy info
        self.stdout.write('\n📚 Canonical Taxonomy:')
        self.stdout.write('   Grades: ' + ', '.join([f'{code} ({name})' for code, name in GRADE_CHOICES]))
        self.stdout.write('\n   Topics:')
        for code, name in TOPIC_CHOICES:
            self.stdout.write(f'     • {name}')

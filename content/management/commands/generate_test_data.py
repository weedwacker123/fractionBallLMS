from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from content.models import VideoAsset, Resource, Playlist, PlaylistItem, GRADE_CHOICES, TOPIC_CHOICES
from accounts.models import School
import random
from datetime import datetime, timedelta
import uuid

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate large-scale test data for performance testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--videos',
            type=int,
            default=1000,
            help='Number of videos to create (default: 1000)'
        )
        parser.add_argument(
            '--resources',
            type=int,
            default=500,
            help='Number of resources to create (default: 500)'
        )
        parser.add_argument(
            '--playlists',
            type=int,
            default=100,
            help='Number of playlists to create (default: 100)'
        )
        parser.add_argument(
            '--schools',
            type=int,
            default=5,
            help='Number of additional schools to create (default: 5)'
        )
        parser.add_argument(
            '--teachers-per-school',
            type=int,
            default=20,
            help='Number of teachers per school (default: 20)'
        )

    def handle(self, *args, **options):
        videos_count = options['videos']
        resources_count = options['resources']
        playlists_count = options['playlists']
        schools_count = options['schools']
        teachers_per_school = options['teachers_per_school']

        self.stdout.write(self.style.SUCCESS('🚀 Generating large-scale test data...'))
        self.stdout.write(f'Target: {videos_count} videos, {resources_count} resources, {playlists_count} playlists')

        # Create additional schools if needed
        existing_schools = list(School.objects.all())
        if len(existing_schools) < schools_count:
            self.create_schools(schools_count - len(existing_schools))
        
        schools = list(School.objects.all()[:schools_count])
        
        # Create additional teachers
        self.create_teachers(schools, teachers_per_school)
        teachers = list(User.objects.filter(role__in=['TEACHER', 'SCHOOL_ADMIN']))

        # Generate content in batches for better performance
        batch_size = 100
        
        # Generate videos
        self.stdout.write('📹 Generating videos...')
        self.generate_videos_batch(videos_count, teachers, batch_size)
        
        # Generate resources
        self.stdout.write('📄 Generating resources...')
        self.generate_resources_batch(resources_count, teachers, batch_size)
        
        # Generate playlists
        self.stdout.write('📋 Generating playlists...')
        self.generate_playlists_batch(playlists_count, teachers)
        
        # Final statistics
        self.print_statistics()

    def create_schools(self, count):
        """Create additional schools"""
        school_names = [
            'Riverside Elementary', 'Oakwood Middle School', 'Pine Valley High',
            'Maple Grove Academy', 'Sunset Elementary', 'Mountain View School',
            'Cedar Creek Elementary', 'Willowbrook Middle', 'Heritage High School',
            'Spring Valley Academy', 'Brookside Elementary', 'Forest Hills School'
        ]
        
        schools_to_create = []
        for i in range(count):
            base_name = random.choice(school_names)
            schools_to_create.append(School(
                name=f"{base_name} #{i+1}",
                domain=f"school{len(School.objects.all()) + i + 1}",
                address=f"{random.randint(100, 9999)} Education Ave, Learning City, LC {random.randint(10000, 99999)}",
                phone=f"555-{random.randint(1000, 9999)}",
                is_active=True
            ))
        
        School.objects.bulk_create(schools_to_create)
        self.stdout.write(f'✅ Created {count} additional schools')

    def create_teachers(self, schools, teachers_per_school):
        """Create additional teachers"""
        first_names = [
            'Emma', 'Liam', 'Olivia', 'Noah', 'Ava', 'William', 'Sophia', 'James',
            'Isabella', 'Oliver', 'Charlotte', 'Benjamin', 'Amelia', 'Lucas', 'Mia',
            'Henry', 'Harper', 'Alexander', 'Evelyn', 'Mason', 'Abigail', 'Michael',
            'Emily', 'Ethan', 'Elizabeth', 'Daniel', 'Sofia', 'Matthew', 'Avery', 'Aiden'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
            'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
            'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Lewis'
        ]
        
        teachers_to_create = []
        for school in schools:
            existing_count = User.objects.filter(school=school).count()
            needed = max(0, teachers_per_school - existing_count)
            
            for i in range(needed):
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                username = f"{first_name.lower()}.{last_name.lower()}.{school.domain}.{i+1}"
                
                # Avoid duplicates
                if User.objects.filter(username=username).exists():
                    username += f".{random.randint(1000, 9999)}"
                
                teachers_to_create.append(User(
                    username=username,
                    email=f"{username}@{school.domain}.edu",
                    first_name=first_name,
                    last_name=last_name,
                    role=random.choices(
                        ['TEACHER', 'SCHOOL_ADMIN'], 
                        weights=[0.9, 0.1]
                    )[0],
                    school=school,
                    firebase_uid=f"teacher_{uuid.uuid4().hex}",
                    phone=f"555-{random.randint(1000, 9999)}",
                    is_active=True
                ))
        
        if teachers_to_create:
            User.objects.bulk_create(teachers_to_create)
            self.stdout.write(f'✅ Created {len(teachers_to_create)} additional teachers')

    def generate_videos_batch(self, total_count, teachers, batch_size):
        """Generate videos in batches"""
        video_titles = self.get_video_titles()
        descriptions = self.get_descriptions()
        tags_pool = [
            'visual', 'interactive', 'beginner', 'intermediate', 'advanced',
            'problem-solving', 'real-world', 'hands-on', 'conceptual', 'procedural',
            'games', 'activities', 'assessment', 'review', 'tutorial', 'practice',
            'demonstration', 'explanation', 'example', 'step-by-step'
        ]
        
        created_count = 0
        batch_num = 1
        
        while created_count < total_count:
            current_batch_size = min(batch_size, total_count - created_count)
            videos_batch = []
            
            for i in range(current_batch_size):
                teacher = random.choice(teachers)
                grade = random.choice([choice[0] for choice in GRADE_CHOICES])
                topic = random.choice([choice[0] for choice in TOPIC_CHOICES])
                
                # Get topic-specific titles
                topic_titles = video_titles.get(topic, ['Educational Video'])
                title = random.choice(topic_titles)
                
                # Add variation to titles
                if random.random() < 0.3:
                    title += f" - Part {random.randint(1, 3)}"
                elif random.random() < 0.2:
                    title += f" ({random.choice(['Advanced', 'Beginner', 'Review', 'Practice'])})"
                
                # Create realistic timestamps (distributed over past year)
                days_ago = random.randint(1, 365)
                created_at = timezone.now() - timedelta(days=days_ago)
                
                videos_batch.append(VideoAsset(
                    title=title,
                    description=random.choice(descriptions),
                    grade=grade,
                    topic=topic,
                    tags=random.sample(tags_pool, random.randint(2, 6)),
                    duration=random.randint(180, 2400),  # 3-40 minutes
                    file_size=random.randint(50000000, 800000000),  # 50MB-800MB
                    storage_uri=f'https://firebasestorage.googleapis.com/v0/b/project/o/videos%2F{created_at.strftime("%Y/%m/%d")}%2F{uuid.uuid4()}.mp4',
                    thumbnail_uri=f'https://firebasestorage.googleapis.com/v0/b/project/o/thumbnails%2F{created_at.strftime("%Y/%m/%d")}%2F{uuid.uuid4()}.jpg',
                    owner=teacher,
                    school=teacher.school,
                    status=random.choices(
                        ['DRAFT', 'PENDING', 'PUBLISHED', 'PUBLISHED'], 
                        weights=[0.1, 0.1, 0.4, 0.4]
                    )[0],  # More published content
                    created_at=created_at,
                    updated_at=created_at + timedelta(hours=random.randint(0, 48))
                ))
            
            # Bulk create batch
            with transaction.atomic():
                VideoAsset.objects.bulk_create(videos_batch)
            
            created_count += len(videos_batch)
            self.stdout.write(f'  📹 Batch {batch_num}: Created {len(videos_batch)} videos ({created_count}/{total_count})')
            batch_num += 1

    def generate_resources_batch(self, total_count, teachers, batch_size):
        """Generate resources in batches"""
        resource_titles = [
            'Fraction Worksheet - Basic Practice', 'Equivalent Fractions Activity Sheet',
            'Fraction Number Line Template', 'Mixed Numbers Practice Problems',
            'Fraction Games and Activities Guide', 'Assessment Rubric for Fractions',
            'Parent Guide to Fractions', 'Fraction Vocabulary Cards',
            'Real-World Fraction Problems', 'Fraction Art Project Instructions',
            'Interactive Fraction Games', 'Fraction Story Problems Collection',
            'Visual Fraction Models', 'Fraction Comparison Charts',
            'Hands-On Fraction Activities', 'Fraction Assessment Tools'
        ]
        
        file_types = ['pdf', 'doc', 'docx', 'ppt', 'pptx', 'xlsx', 'txt']
        descriptions = self.get_descriptions()
        tags_pool = ['worksheet', 'practice', 'assessment', 'activity', 'guide', 'template', 'games']
        
        created_count = 0
        batch_num = 1
        
        while created_count < total_count:
            current_batch_size = min(batch_size, total_count - created_count)
            resources_batch = []
            
            for i in range(current_batch_size):
                teacher = random.choice(teachers)
                file_type = random.choice(file_types)
                
                # Create realistic timestamps
                days_ago = random.randint(1, 365)
                created_at = timezone.now() - timedelta(days=days_ago)
                
                resources_batch.append(Resource(
                    title=random.choice(resource_titles),
                    description=random.choice(descriptions),
                    file_uri=f'https://firebasestorage.googleapis.com/v0/b/project/o/resources%2F{created_at.strftime("%Y/%m/%d")}%2F{uuid.uuid4()}.{file_type}',
                    file_type=file_type,
                    file_size=random.randint(100000, 50000000),  # 100KB-50MB
                    grade=random.choice([choice[0] for choice in GRADE_CHOICES]) if random.random() < 0.8 else '',
                    topic=random.choice([choice[0] for choice in TOPIC_CHOICES]) if random.random() < 0.8 else '',
                    tags=random.sample(tags_pool, random.randint(1, 4)),
                    owner=teacher,
                    school=teacher.school,
                    status=random.choices(['DRAFT', 'PUBLISHED'], weights=[0.2, 0.8])[0],
                    created_at=created_at,
                    updated_at=created_at + timedelta(hours=random.randint(0, 24))
                ))
            
            # Bulk create batch
            with transaction.atomic():
                Resource.objects.bulk_create(resources_batch)
            
            created_count += len(resources_batch)
            self.stdout.write(f'  📄 Batch {batch_num}: Created {len(resources_batch)} resources ({created_count}/{total_count})')
            batch_num += 1

    def generate_playlists_batch(self, total_count, teachers):
        """Generate playlists with items"""
        playlist_names = [
            'Introduction to Fractions Unit', 'Equivalent Fractions Lessons',
            'Fraction Operations Complete Course', 'Visual Fraction Models',
            'Real-World Fraction Applications', 'Assessment and Review Videos',
            'Advanced Fraction Concepts', 'Fraction Games and Activities',
            'Parent Resources for Fractions', 'Differentiated Fraction Instruction',
            'Grade {} Fraction Curriculum', 'Fraction Remediation Resources',
            'Advanced Problem Solving', 'Interactive Fraction Lessons'
        ]
        
        created_count = 0
        
        for i in range(total_count):
            teacher = random.choice(teachers)
            
            # Get published videos from the same school
            school_videos = list(VideoAsset.objects.filter(
                school=teacher.school,
                status='PUBLISHED'
            ).order_by('?')[:random.randint(3, 12)])
            
            if school_videos:
                playlist_name = random.choice(playlist_names)
                if '{}' in playlist_name:
                    grade = random.choice([choice[1] for choice in GRADE_CHOICES])
                    playlist_name = playlist_name.format(grade)
                
                # Create realistic timestamp
                days_ago = random.randint(1, 180)
                created_at = timezone.now() - timedelta(days=days_ago)
                
                playlist = Playlist.objects.create(
                    name=playlist_name,
                    description=f'Curated collection of {len(school_videos)} videos for effective fraction instruction.',
                    owner=teacher,
                    school=teacher.school,
                    is_public=random.choice([True, False]),
                    created_at=created_at,
                    updated_at=created_at + timedelta(hours=random.randint(0, 72))
                )
                
                # Add videos to playlist
                playlist_items = []
                for order, video in enumerate(school_videos, 1):
                    playlist_items.append(PlaylistItem(
                        playlist=playlist,
                        video_asset=video,
                        order=order,
                        notes=f'Video {order} in the sequence' if random.random() < 0.3 else '',
                        created_at=created_at + timedelta(minutes=order * 5)
                    ))
                
                PlaylistItem.objects.bulk_create(playlist_items)
                created_count += 1
                
                if created_count % 10 == 0:
                    self.stdout.write(f'  📋 Created {created_count}/{total_count} playlists')
        
        self.stdout.write(f'✅ Created {created_count} playlists with items')

    def get_video_titles(self):
        """Get topic-specific video titles"""
        return {
            'fractions_basics': [
                'Introduction to Fractions', 'What is a Fraction?', 'Parts of a Whole',
                'Fraction Vocabulary', 'Understanding Numerators and Denominators',
                'Fractions in Everyday Life', 'Basic Fraction Concepts'
            ],
            'equivalent_fractions': [
                'Finding Equivalent Fractions', 'Simplifying Fractions', 'Common Denominators',
                'Fraction Strips and Equivalents', 'Visual Models for Equivalent Fractions',
                'Reducing Fractions to Lowest Terms', 'Equivalent Fraction Patterns'
            ],
            'comparing_ordering': [
                'Comparing Fractions with Same Denominators', 'Comparing Different Denominators',
                'Ordering Fractions from Least to Greatest', 'Using Benchmark Fractions',
                'Greater Than, Less Than, or Equal', 'Fraction Comparison Strategies'
            ],
            'number_line': [
                'Fractions on a Number Line', 'Placing Fractions Between Whole Numbers',
                'Number Line Strategies', 'Estimating Fraction Positions',
                'Number Line Games and Activities', 'Visualizing Fractions'
            ],
            'mixed_improper': [
                'Mixed Numbers vs Improper Fractions', 'Converting Mixed to Improper',
                'Converting Improper to Mixed', 'When to Use Each Form',
                'Real-World Mixed Number Examples', 'Mixed Number Operations'
            ],
            'add_subtract_fractions': [
                'Adding Fractions with Same Denominators', 'Subtracting Same Denominators',
                'Adding Different Denominators', 'Subtracting Different Denominators',
                'Adding and Subtracting Mixed Numbers', 'Fraction Addition Strategies'
            ],
            'multiply_divide_fractions': [
                'Multiplying Fractions by Whole Numbers', 'Multiplying Two Fractions',
                'Dividing Fractions', 'Reciprocals and Division',
                'Real-World Multiplication and Division', 'Advanced Fraction Operations'
            ],
            'decimals_percents': [
                'Fractions to Decimals', 'Decimals to Fractions', 'Introduction to Percentages',
                'Fractions, Decimals, and Percents', 'Converting Between Forms',
                'Decimal and Percent Applications'
            ],
            'ratio_proportion': [
                'Introduction to Ratios', 'Understanding Proportions', 'Solving Proportions',
                'Scale Drawings and Maps', 'Real-World Ratio Problems', 'Ratio Applications'
            ],
            'word_problems': [
                'Fraction Word Problem Strategies', 'Identifying Key Information',
                'Drawing Pictures for Word Problems', 'Multi-Step Fraction Problems',
                'Real-World Applications', 'Problem-Solving Techniques'
            ]
        }

    def get_descriptions(self):
        """Get realistic descriptions"""
        return [
            'This comprehensive video introduces key mathematical concepts with clear examples and visual aids designed to help students understand complex topics.',
            'Step-by-step explanation with practice problems included to reinforce learning and build confidence in mathematical problem-solving skills.',
            'Interactive lesson with real-world applications and examples that connect mathematical concepts to everyday situations and experiences.',
            'Comprehensive overview with multiple solution strategies to help students find the approach that works best for their learning style.',
            'Engaging presentation with visual models and manipulatives that make abstract concepts concrete and accessible to all learners.',
            'Detailed walkthrough with common mistakes highlighted and strategies provided to avoid them, building stronger mathematical understanding.',
            'Fun and interactive approach to learning this important concept through games, activities, and hands-on exploration of mathematical ideas.',
            'Clear explanations with plenty of practice opportunities to build fluency and confidence in mathematical skills and problem-solving.',
            'Research-based instructional strategies combined with engaging content to support diverse learning needs and preferences.',
            'Standards-aligned content designed to support classroom instruction and help students achieve grade-level mathematical proficiency.'
        ]

    def print_statistics(self):
        """Print final statistics"""
        total_videos = VideoAsset.objects.count()
        total_resources = Resource.objects.count()
        total_playlists = Playlist.objects.count()
        total_schools = School.objects.count()
        total_teachers = User.objects.filter(role__in=['TEACHER', 'SCHOOL_ADMIN']).count()
        
        # Performance statistics
        published_videos = VideoAsset.objects.filter(status='PUBLISHED').count()
        published_resources = Resource.objects.filter(status='PUBLISHED').count()
        
        self.stdout.write('\n' + '='*80)
        self.stdout.write(
            self.style.SUCCESS(
                f'🎉 Large-scale test data generation completed!\n\n'
                f'📊 Final Statistics:\n'
                f'   • Schools: {total_schools}\n'
                f'   • Teachers: {total_teachers}\n'
                f'   • Videos: {total_videos} ({published_videos} published)\n'
                f'   • Resources: {total_resources} ({published_resources} published)\n'
                f'   • Playlists: {total_playlists}\n\n'
                f'🚀 Performance Test Ready:\n'
                f'   • Library queries should handle {published_videos + published_resources} items\n'
                f'   • Database indexes optimized for filtering and search\n'
                f'   • Content distributed across {total_schools} schools\n\n'
                f'✨ Ready for load testing with realistic data volumes!'
            )
        )


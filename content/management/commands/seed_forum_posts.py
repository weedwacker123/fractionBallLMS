"""
Management command to seed sample forum posts
"""
from django.core.management.base import BaseCommand
from content.models import ForumPost, ForumCategory, ForumComment
from accounts.models import User
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = 'Seed sample forum posts and comments'
    
    def handle(self, *args, **options):
        self.stdout.write('Seeding forum posts...')
        
        # Get or create a system user for sample posts
        system_user, _ = User.objects.get_or_create(
            username='demo_teacher',
            defaults={
                'email': 'demo@fractionball.com',
                'first_name': 'Demo',
                'last_name': 'Teacher',
                'role': 'TEACHER'
            }
        )
        
        # Get categories
        general = ForumCategory.objects.get(slug='general')
        tips = ForumCategory.objects.get(slug='activity-tips')
        questions = ForumCategory.objects.get(slug='questions')
        success = ForumCategory.objects.get(slug='success-stories')
        
        sample_posts = [
            {
                'title': 'Tips for Managing Field Cone Frenzy with Large Classes',
                'slug': 'tips-field-cone-frenzy-large-classes',
                'content': '''I've been using Field Cone Frenzy with my 5th graders and wanted to share some management strategies that have worked well with larger classes (25+ students):

1. **Divide into 4-5 teams** instead of just 2-3. This reduces wait time and keeps everyone engaged.

2. **Use multiple courts** if available. We use both the main basketball court and set up a mini court in the gym.

3. **Assign specific roles**: shooter, cone collector, fraction calculator, and timer. Rotate roles every 3 minutes.

4. **Pre-label cones** with fraction values before class to save setup time.

5. **Create a "fraction bank"** where students can trade cones for equivalent fractions.

Has anyone else tried these strategies? What works for you?''',
                'category': tips,
                'is_pinned': True,
                'view_count': 234,
                'created_at': timezone.now() - timedelta(days=2)
            },
            {
                'title': 'Adapting Activities for Different Grade Levels',
                'slug': 'adapting-activities-different-grades',
                'content': '''Has anyone successfully adapted the Grade 5 activities for Grade 3 or 4 students? I'd love to hear your modifications.

I'm thinking about:
- Simplifying the fraction operations for younger students
- Using larger denominators that are easier to visualize
- Adding more scaffolding and visual aids

What has worked in your classroom?''',
                'category': questions,
                'view_count': 156,
                'created_at': timezone.now() - timedelta(days=7)
            },
            {
                'title': 'Amazing Results with Bottle-Cap Bonanza!',
                'slug': 'amazing-results-bottle-cap-bonanza',
                'content': '''Just wanted to share that my students absolutely LOVED Bottle-Cap Bonanza today! 

We did the activity after spring break and I was worried they'd forgotten their fractions, but the hands-on nature really helped them reconnect with the concepts.

Three students who usually struggle with equivalent fractions were explaining the concepts to their peers by the end of class. The bottle caps made it so concrete and visual.

Thank you Fraction Ball team for creating such engaging activities! 🏀📚''',
                'category': success,
                'view_count': 89,
                'created_at': timezone.now() - timedelta(days=3)
            },
            {
                'title': 'Best Practices for Classroom vs Court Activities',
                'slug': 'best-practices-classroom-court',
                'content': '''For teachers who are new to Fraction Ball, here are some tips I've learned about when to use classroom vs court activities:

**Classroom Activities (like Bottle-Cap Bonanza):**
- Great for focused, detail-oriented work
- Better for first introducing new concepts
- Easier to monitor individual student understanding
- Less setup and cleanup time

**Court Activities (like Field Cone Frenzy):**
- Excellent for review and practice
- Students get physical activity
- Builds teamwork and communication skills
- More engaging for kinesthetic learners

I try to alternate between the two to keep things fresh. What's your approach?''',
                'category': tips,
                'view_count': 178,
                'created_at': timezone.now() - timedelta(days=5)
            },
        ]
        
        created_count = 0
        
        for post_data in sample_posts:
            post, created = ForumPost.objects.get_or_create(
                slug=post_data['slug'],
                defaults={
                    **post_data,
                    'author': system_user,
                    'last_activity_at': post_data['created_at']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {post.title}')
                )
                
                # Add sample comments
                if post.slug == 'tips-field-cone-frenzy-large-classes':
                    ForumComment.objects.create(
                        post=post,
                        author=system_user,
                        content="Great tips! I especially love the role rotation idea. Keeps everyone engaged!",
                        created_at=post.created_at + timedelta(hours=2)
                    )
                    comment2 = ForumComment.objects.create(
                        post=post,
                        author=system_user,
                        content="The fraction bank is genius! I'm definitely trying that.",
                        created_at=post.created_at + timedelta(hours=5)
                    )
                    post.last_activity_at = comment2.created_at
                    post.save()
                
                elif post.slug == 'adapting-activities-different-grades':
                    ForumComment.objects.create(
                        post=post,
                        author=system_user,
                        content="I've adapted Field Cone Frenzy for Grade 3 by using only halves, thirds, and fourths. Works great!",
                        created_at=post.created_at + timedelta(hours=12)
                    )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_count} forum posts with sample comments!'
            )
        )


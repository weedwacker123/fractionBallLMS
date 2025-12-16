"""
Management command to seed activities for V4 interface
"""
from django.core.management.base import BaseCommand
from content.models import Activity
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seed initial activities for Fraction Ball V4 interface'
    
    def handle(self, *args, **options):
        self.stdout.write('Seeding activities...')
        
        activities_data = [
            {
                'title': 'Field Cone Frenzy',
                'slug': 'field-cone-frenzy',
                'description': 'Students practice shooting basketballs while collecting cones to learn about mixed denominators and mixed numbers.',
                'activity_number': 1,
                'grade': '5',
                'topics': ['Mixed Denominators', 'Mixed Numbers'],
                'location': 'court',
                'icon_type': 'cone',
                'prerequisites': [
                    'Shooting a basketball',
                    'Making teams',
                    'Understanding fractions basics'
                ],
                'learning_objectives': 'Students will be able to:\n• Add and subtract fractions with mixed denominators\n• Convert between mixed numbers and improper fractions\n• Apply fraction operations in a physical activity context',
                'materials': [
                    'Basketball',
                    'Cones (at least 10)',
                    'Court or large open space',
                    'Fraction cards',
                    'Scoresheet'
                ],
                'game_rules': [
                    'Teacher divides class into two teams',
                    'One player shoots the basketball at the hoop',
                    'If they make the shot, their team collects a cone',
                    'Each cone has a fraction value',
                    'Teams must add their fraction values correctly to score points',
                    'First team to reach the target fraction wins'
                ],
                'key_terms': {
                    'Mixed Number': 'A number containing both a whole number and a proper fraction',
                    'Improper Fraction': 'A fraction where the numerator is greater than or equal to the denominator',
                    'Common Denominator': 'A shared multiple of two or more denominators'
                },
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Bottle-Cap Bonanza',
                'slug': 'bottle-cap-bonanza',
                'description': 'Students learn equivalent fractions through bottle cap collection and sorting activities.',
                'activity_number': 2,
                'grade': '5',
                'topics': ['Equivalent Fractions'],
                'location': 'classroom',
                'icon_type': 'bottle-cap',
                'prerequisites': [
                    'Understanding basic fractions',
                    'Ability to compare fractions',
                    'Working in groups'
                ],
                'learning_objectives': 'Students will be able to:\n• Identify equivalent fractions\n• Create equivalent fractions by multiplying numerator and denominator\n• Compare fractions by finding common denominators',
                'materials': [
                    'Bottle caps (various colors)',
                    'Fraction cards',
                    'Sorting trays',
                    'Markers',
                    'Worksheets'
                ],
                'game_rules': [
                    'Students work in teams of 3-4',
                    'Each team receives a collection of bottle caps',
                    'Caps are labeled with different fractions',
                    'Teams must sort caps into groups of equivalent fractions',
                    'Teams earn points for correct groupings',
                    'Bonus points for finding the most equivalents'
                ],
                'key_terms': {
                    'Equivalent Fractions': 'Fractions that represent the same value even though they have different numerators and denominators',
                    'Simplify': 'To reduce a fraction to its simplest form',
                    'Scale': 'To multiply or divide both numerator and denominator by the same number'
                },
                'is_published': True,
                'order': 2
            },
            {
                'title': 'Simon Says & Switch',
                'slug': 'simon-says-switch',
                'description': 'Students practice fraction operations through movement and following directions in this active game.',
                'activity_number': 3,
                'grade': '5',
                'topics': ['Mixed Denominators', 'Like Denominators', 'Addition', 'Subtraction'],
                'location': 'both',
                'icon_type': 'person',
                'prerequisites': [
                    'Following multi-step directions',
                    'Understanding fraction operations',
                    'Basic movement skills'
                ],
                'learning_objectives': 'Students will be able to:\n• Add and subtract fractions with like denominators\n• Add and subtract fractions with unlike denominators\n• Apply mental math strategies for fractions',
                'materials': [
                    'Fraction cards (large, visible)',
                    'Movement space',
                    'Whistle or bell',
                    'Score cards',
                    'Timer'
                ],
                'game_rules': [
                    'Teacher calls out "Simon Says" followed by a fraction operation',
                    'Students must physically represent the answer (e.g., jump 3/4 of the way across)',
                    'When "Switch" is called, students must switch fraction problems with a partner',
                    'Students work collaboratively to solve',
                    'Points awarded for correct representations and solutions'
                ],
                'key_terms': {
                    'Like Denominators': 'Fractions that have the same denominator',
                    'Unlike Denominators': 'Fractions that have different denominators',
                    'Operation': 'A mathematical process (addition, subtraction, etc.)'
                },
                'is_published': True,
                'order': 3
            },
            {
                'title': 'Field Cone Frenzy Pt. 2',
                'slug': 'field-cone-frenzy-pt2',
                'description': 'Advanced version of Field Cone Frenzy with more complex fraction operations and competitive elements.',
                'activity_number': 1,
                'grade': '5',
                'topics': ['Field Goals Frenzy', 'Advanced Mixed Numbers'],
                'location': 'court',
                'icon_type': 'cone',
                'prerequisites': [
                    'Completed Field Cone Frenzy Part 1',
                    'Confident with mixed denominators',
                    'Ready for competitive play'
                ],
                'learning_objectives': 'Students will be able to:\n• Perform multi-step fraction operations\n• Apply strategic thinking with fractions\n• Work under time pressure with fraction calculations',
                'materials': [
                    'Basketball',
                    'Cones (at least 15)',
                    'Court or large open space',
                    'Advanced fraction cards',
                    'Timer',
                    'Scoresheet'
                ],
                'game_rules': [
                    'Teams compete in timed rounds',
                    'Each successful shot allows the team to collect multiple cones',
                    'Teams must perform multi-step fraction operations',
                    'Strategic bonus rounds with multiplier effects',
                    'Team with highest fraction score wins'
                ],
                'key_terms': {
                    'Multi-step Operation': 'A problem requiring more than one mathematical step',
                    'Strategy': 'A plan of action to achieve a goal',
                    'Multiplier': 'A number that multiplies another number'
                },
                'is_published': True,
                'order': 4
            },
            {
                'title': 'Bottle-cap Bonanza Pt. 2',
                'slug': 'bottle-cap-bonanza-pt2',
                'description': 'Advanced equivalent fractions activity with fraction operations and real-world applications.',
                'activity_number': 2,
                'grade': '5',
                'topics': ['Equivalent Fractions', 'Fraction Operations'],
                'location': 'classroom',
                'icon_type': 'bottle-cap',
                'prerequisites': [
                    'Completed Bottle-cap Bonanza Part 1',
                    'Strong understanding of equivalent fractions',
                    'Ready for challenge activities'
                ],
                'learning_objectives': 'Students will be able to:\n• Create complex equivalent fractions\n• Apply equivalent fractions to solve word problems\n• Use equivalent fractions in measurement contexts',
                'materials': [
                    'Bottle caps (more variety)',
                    'Advanced fraction cards',
                    'Measuring tools',
                    'Word problem cards',
                    'Recording sheets'
                ],
                'game_rules': [
                    'Teams receive word problems requiring equivalent fractions',
                    'Must use bottle caps to model solutions',
                    'Create visual representations of equivalents',
                    'Present solutions to class',
                    'Points for accuracy and creativity'
                ],
                'key_terms': {
                    'Model': 'To represent a mathematical concept physically or visually',
                    'Application': 'Using math in real-world contexts',
                    'Representation': 'A way of showing a mathematical idea'
                },
                'is_published': True,
                'order': 5
            },
            {
                'title': 'Simon Says Pt. 2',
                'slug': 'simon-says-pt2',
                'description': 'Advanced movement-based fraction game with multiplication and division of fractions.',
                'activity_number': 3,
                'grade': '5',
                'topics': ['Mixed Denominators', 'Multiplication', 'Division'],
                'location': 'both',
                'icon_type': 'person',
                'prerequisites': [
                    'Completed Simon Says & Switch Part 1',
                    'Understanding fraction multiplication',
                    'Ready for faster-paced activities'
                ],
                'learning_objectives': 'Students will be able to:\n• Multiply and divide fractions\n• Apply fraction operations to measurement\n• Work collaboratively on complex problems',
                'materials': [
                    'Fraction operation cards',
                    'Large movement space',
                    'Measuring tape',
                    'Timer',
                    'Score tracker'
                ],
                'game_rules': [
                    'Faster-paced version with multiplication and division',
                    'Students must calculate and move simultaneously',
                    'Partner challenges with fraction operations',
                    'Relay race format with fraction stations',
                    'Team with most correct operations wins'
                ],
                'key_terms': {
                    'Fraction Multiplication': 'Multiplying numerators together and denominators together',
                    'Fraction Division': 'Multiplying by the reciprocal of the divisor',
                    'Reciprocal': 'A fraction flipped upside down'
                },
                'is_published': True,
                'order': 6
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for activity_data in activities_data:
            activity, created = Activity.objects.update_or_create(
                slug=activity_data['slug'],
                defaults=activity_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created: {activity.title}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {activity.title}')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_count} new activities and updated {updated_count} existing activities!'
            )
        )


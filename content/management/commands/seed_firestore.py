"""
Management command to seed Firestore with initial activities data
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from firebase_admin import firestore
import firebase_admin
from datetime import datetime


def get_firestore_client():
    """Get Firestore client with explicit database name and credentials"""
    from google.cloud import firestore as gc_firestore
    from google.oauth2 import service_account
    from django.conf import settings

    # Use service account credentials from Django settings
    credentials = service_account.Credentials.from_service_account_info(
        settings.FIREBASE_CONFIG
    )

    # Use google-cloud-firestore directly with explicit database='default'
    # Note: The database is named 'default' (not '(default)') in this project
    return gc_firestore.Client(
        project='fractionball-lms',
        database='default',
        credentials=credentials
    )


class Command(BaseCommand):
    help = 'Seed Firestore with initial activities for Fraction Ball LMS'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing activities before seeding',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        clear = options.get('clear', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be written'))

        db = get_firestore_client()

        if clear and not dry_run:
            self.stdout.write('Clearing existing activities...')
            docs = db.collection('activities').stream()
            for doc in docs:
                doc.reference.delete()
            self.stdout.write(self.style.SUCCESS('Cleared existing activities'))

        self.stdout.write('Seeding activities to Firestore...')

        activities_data = self.get_activities_data()

        created_count = 0
        for activity in activities_data:
            if dry_run:
                self.stdout.write(f"  Would create: {activity['title']} (Grade {activity['grade']})")
            else:
                # Convert to Firestore format
                firestore_data = self.convert_to_firestore_format(activity)
                db.collection('activities').add(firestore_data)
                self.stdout.write(f"  Created: {activity['title']}")
            created_count += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f'Would create {created_count} activities'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Successfully seeded {created_count} activities'))

    def convert_to_firestore_format(self, activity):
        """Convert Django-style activity data to Firestore format"""
        # Convert grade to number for gradeLevel array
        grade = activity.get('grade', '5')
        grade_num = 0 if grade == 'K' else int(grade)

        return {
            'title': activity['title'],
            'slug': activity.get('slug', slugify(activity['title'])),
            'description': activity.get('description', ''),
            'gradeLevel': [grade_num],
            'activityNumber': activity.get('activity_number', 1),
            'order': activity.get('order', 0),
            'location': activity.get('location', 'classroom'),
            'iconType': activity.get('icon_type', 'cone'),
            'tags': activity.get('topics', []),
            'taxonomy': {
                'topic': activity.get('topics', [''])[0] if activity.get('topics') else '',
                'courtType': activity.get('location', ''),
            },
            'prerequisites': activity.get('prerequisites', []),
            'learningObjectives': activity.get('learning_objectives', ''),
            'materials': activity.get('materials', []),
            'gameRules': activity.get('game_rules', []),
            'keyTerms': activity.get('key_terms', {}),
            'videos': [],  # Empty - to be added via FireCMS
            'resources': [],  # Empty - to be added via FireCMS
            'lessonPdf': '',  # Empty - to be added via FireCMS
            'thumbnailUrl': '',
            'status': 'published' if activity.get('is_published', True) else 'draft',
            'createdAt': datetime.utcnow(),
            'updatedAt': datetime.utcnow(),
        }

    def get_activities_data(self):
        """Return the K-8 curriculum activities data"""
        return [
            # KINDERGARTEN
            {
                'title': 'Half & Half Hoops',
                'slug': 'half-half-hoops-k',
                'description': 'Kindergartners learn about halves by splitting groups of balls and sharing equally.',
                'activity_number': 1,
                'grade': 'K',
                'topics': ['Fractions Basics', 'Equal Parts'],
                'location': 'court',
                'icon_type': 'ball',
                'prerequisites': ['Counting to 10', 'Understanding "same" and "different"', 'Basic throwing skills'],
                'learning_objectives': 'Students will be able to:\n• Identify two equal parts (halves)\n• Split a group into two equal parts\n• Use the word "half" correctly',
                'materials': ['Soft balls (10)', 'Two buckets', 'Number cards'],
                'game_rules': ['Teacher shows a group of balls', 'Students count the total', 'Class splits balls into two equal buckets', 'Students practice saying "half"', 'Repeat with different amounts'],
                'key_terms': {'Half': 'One of two equal parts', 'Equal': 'The same amount', 'Whole': 'All of something'},
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Quarter Catch',
                'slug': 'quarter-catch-k',
                'description': 'Students explore quarters by dividing items into four equal groups.',
                'activity_number': 2,
                'grade': 'K',
                'topics': ['Fractions Basics', 'Equal Parts'],
                'location': 'classroom',
                'icon_type': 'hands',
                'prerequisites': ['Understanding halves', 'Counting to 20', 'Fine motor skills'],
                'learning_objectives': 'Students will be able to:\n• Identify four equal parts (quarters)\n• Split items into four groups\n• Compare halves and quarters',
                'materials': ['Play dough', 'Plastic knives', 'Paper circles', 'Crayons'],
                'game_rules': ['Students receive a ball of play dough', 'First, split into halves', 'Then, split each half again', 'Count the four equal pieces', 'Color paper circles to show quarters'],
                'key_terms': {'Quarter': 'One of four equal parts', 'Fourth': 'Same as a quarter', 'Divide': 'To split into parts'},
                'is_published': True,
                'order': 2
            },
            # GRADE 1
            {
                'title': 'Pizza Party Fractions',
                'slug': 'pizza-party-fractions-1',
                'description': 'First graders learn fractions by sharing pretend pizzas equally among friends.',
                'activity_number': 1,
                'grade': '1',
                'topics': ['Fractions Basics', 'Equal Parts'],
                'location': 'classroom',
                'icon_type': 'pizza',
                'prerequisites': ['Understanding halves and quarters', 'Counting skills', 'Sharing concepts'],
                'learning_objectives': 'Students will be able to:\n• Divide shapes into 2, 3, and 4 equal parts\n• Name the parts (halves, thirds, fourths)\n• Understand fair sharing',
                'materials': ['Paper plates', 'Scissors', 'Markers', 'Fraction circles'],
                'game_rules': ['Students create paper "pizzas"', 'Fold and cut into equal slices', 'Practice sharing with 2, 3, or 4 friends', 'Name each piece using fraction words', 'Compare sizes of different pieces'],
                'key_terms': {'Third': 'One of three equal parts', 'Equal Parts': 'Pieces that are the same size', 'Share': 'To divide fairly'},
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Fraction Hopscotch',
                'slug': 'fraction-hopscotch-1',
                'description': 'Students hop through a fraction course, identifying halves, thirds, and fourths.',
                'activity_number': 2,
                'grade': '1',
                'topics': ['Fractions Basics', 'Equal Parts'],
                'location': 'court',
                'icon_type': 'running',
                'prerequisites': ['Physical hopping ability', 'Shape recognition', 'Basic fraction vocabulary'],
                'learning_objectives': 'Students will be able to:\n• Identify fraction names while moving\n• Match shapes to fraction names\n• Build fraction vocabulary through play',
                'materials': ['Chalk or tape', 'Fraction cards', 'Bean bags'],
                'game_rules': ['Create hopscotch with fraction shapes in squares', 'Students hop and call out the fraction name', 'Toss bean bag to a specific fraction', 'Hop to collect it', 'First to identify all fractions wins'],
                'key_terms': {'Identify': 'To recognize and name', 'Fraction': 'A part of a whole', 'Name': 'What we call something'},
                'is_published': True,
                'order': 2
            },
            # GRADE 2
            {
                'title': 'Fraction Relay Race',
                'slug': 'fraction-relay-race-2',
                'description': 'Teams race to match fraction shapes with their names in this active game.',
                'activity_number': 1,
                'grade': '2',
                'topics': ['Equivalent Fractions', 'Fraction Names'],
                'location': 'court',
                'icon_type': 'running',
                'prerequisites': ['Knows halves, thirds, and fourths', 'Can run and follow directions', 'Team cooperation'],
                'learning_objectives': 'Students will be able to:\n• Quickly identify common fractions\n• Match visual fractions to written names\n• Work as a team on math tasks',
                'materials': ['Fraction picture cards', 'Fraction word cards', 'Cones', 'Timer'],
                'game_rules': ['Teams line up at starting line', 'One player runs to card pile', 'Match fraction picture to word', 'Run back and tag next player', 'First team to match all wins'],
                'key_terms': {'Match': 'To find two things that go together', 'Equivalent': 'Equal in value', 'Relay': 'A race where teammates take turns'},
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Number Line Jump',
                'slug': 'number-line-jump-2',
                'description': 'Students physically jump on a giant number line to locate fractions.',
                'activity_number': 2,
                'grade': '2',
                'topics': ['Number Line', 'Fractions Basics'],
                'location': 'court',
                'icon_type': 'number-line',
                'prerequisites': ['Understanding of fractions', 'Counting skills', 'Physical jumping ability'],
                'learning_objectives': 'Students will be able to:\n• Locate fractions on a number line\n• Understand fractions as parts of a whole\n• Compare fraction positions',
                'materials': ['Large number line (tape on floor)', 'Fraction cards', 'Bean bags'],
                'game_rules': ['Create number line from 0 to 1 on floor', 'Draw fraction card', 'Jump to that position on number line', 'Explain your choice', 'Class verifies accuracy'],
                'key_terms': {'Number Line': 'A line showing numbers in order', 'Position': 'Where something is located', 'Between': 'In the middle of two things'},
                'is_published': True,
                'order': 2
            },
            # GRADE 3
            {
                'title': 'Equivalent Fraction Basketball',
                'slug': 'equivalent-fraction-basketball-3',
                'description': 'Students shoot baskets to earn points while finding equivalent fractions.',
                'activity_number': 1,
                'grade': '3',
                'topics': ['Equivalent Fractions'],
                'location': 'court',
                'icon_type': 'basketball',
                'prerequisites': ['Basic fraction understanding', 'Multiplication facts', 'Basketball throwing skills'],
                'learning_objectives': 'Students will be able to:\n• Find equivalent fractions\n• Multiply numerator and denominator by same number\n• Verify equivalence visually',
                'materials': ['Basketball hoop', 'Basketballs', 'Fraction problem cards', 'Scoreboard'],
                'game_rules': ['Draw a fraction card', 'Name an equivalent fraction', 'If correct, take a shot', 'Made baskets earn bonus points', 'Most points wins'],
                'key_terms': {'Equivalent Fractions': 'Fractions that are equal in value', 'Numerator': 'Top number in a fraction', 'Denominator': 'Bottom number in a fraction'},
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Fraction Comparison Toss',
                'slug': 'fraction-comparison-toss-3',
                'description': 'Toss bean bags onto fraction targets and compare which is larger.',
                'activity_number': 2,
                'grade': '3',
                'topics': ['Comparing/Ordering', 'Fractions Basics'],
                'location': 'court',
                'icon_type': 'compare',
                'prerequisites': ['Understanding fractions', 'Comparison concepts', 'Hand-eye coordination'],
                'learning_objectives': 'Students will be able to:\n• Compare two fractions\n• Use >, <, = symbols correctly\n• Explain comparison reasoning',
                'materials': ['Fraction target mats', 'Bean bags', 'Comparison symbol cards', 'Score sheets'],
                'game_rules': ['Two players toss bean bags', 'Each lands on a fraction', 'Compare the two fractions', 'Correct comparison earns point', 'Higher total wins'],
                'key_terms': {'Greater Than': 'Bigger, more', 'Less Than': 'Smaller, fewer', 'Compare': 'To see how things are similar or different'},
                'is_published': True,
                'order': 2
            },
            # GRADE 4
            {
                'title': 'Adding Fractions Soccer',
                'slug': 'adding-fractions-soccer-4',
                'description': 'Score goals by correctly adding fractions with like denominators.',
                'activity_number': 1,
                'grade': '4',
                'topics': ['Add/Subtract Fractions'],
                'location': 'court',
                'icon_type': 'soccer',
                'prerequisites': ['Fraction basics', 'Addition skills', 'Soccer kicking ability'],
                'learning_objectives': 'Students will be able to:\n• Add fractions with like denominators\n• Simplify fraction sums\n• Apply fraction addition in game context',
                'materials': ['Soccer goal', 'Soccer balls', 'Fraction addition cards', 'Answer key'],
                'game_rules': ['Draw addition problem card', 'Solve the fraction addition', 'If correct, take a penalty kick', 'Goals earn team points', 'Most goals wins'],
                'key_terms': {'Like Denominators': 'Same bottom numbers', 'Sum': 'The answer to addition', 'Simplify': 'Reduce to lowest terms'},
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Mixed Number Obstacle Course',
                'slug': 'mixed-number-obstacle-course-4',
                'description': 'Navigate obstacles by converting between mixed numbers and improper fractions.',
                'activity_number': 2,
                'grade': '4',
                'topics': ['Mixed/Improper', 'Equivalent Fractions'],
                'location': 'court',
                'icon_type': 'obstacle',
                'prerequisites': ['Mixed number understanding', 'Improper fractions', 'Physical agility'],
                'learning_objectives': 'Students will be able to:\n• Convert mixed numbers to improper fractions\n• Convert improper fractions to mixed numbers\n• Complete conversions quickly',
                'materials': ['Obstacle course equipment', 'Conversion cards', 'Timer', 'Answer sheets'],
                'game_rules': ['Start at first obstacle', 'Complete conversion to advance', 'Wrong answer means retry', 'Fastest time wins', 'Must complete all conversions'],
                'key_terms': {'Mixed Number': 'Whole number plus fraction', 'Improper Fraction': 'Numerator larger than denominator', 'Convert': 'Change from one form to another'},
                'is_published': True,
                'order': 2
            },
            # GRADE 5
            {
                'title': 'Field Cone Frenzy',
                'slug': 'field-cone-frenzy-5',
                'description': 'Students race to collect cones representing fractions and create equivalent sets.',
                'activity_number': 1,
                'grade': '5',
                'topics': ['Equivalent Fractions', 'Comparing/Ordering'],
                'location': 'court',
                'icon_type': 'cone',
                'prerequisites': ['Equivalent fractions', 'Multiplication and division', 'Physical fitness'],
                'learning_objectives': 'Students will be able to:\n• Identify multiple equivalent fractions\n• Create equivalent fraction sets\n• Compare fractions quickly',
                'materials': ['Colored cones with fractions', 'Collection bags', 'Timer', 'Score sheets'],
                'game_rules': ['Cones scattered on field', 'Find all equivalent fractions', 'Collect matching sets', 'Return to base', 'Most correct sets wins'],
                'key_terms': {'Set': 'A group of related items', 'Equivalent Set': 'Fractions with same value', 'Collect': 'To gather together'},
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Bottle-Cap Bonanza',
                'slug': 'bottle-cap-bonanza-5',
                'description': 'Use bottle caps as fraction manipulatives for adding and subtracting unlike denominators.',
                'activity_number': 2,
                'grade': '5',
                'topics': ['Add/Subtract Fractions', 'Equivalent Fractions'],
                'location': 'classroom',
                'icon_type': 'bottle-cap',
                'prerequisites': ['Adding like denominators', 'Finding common denominators', 'Fraction equivalence'],
                'learning_objectives': 'Students will be able to:\n• Find common denominators\n• Add fractions with unlike denominators\n• Subtract fractions with unlike denominators',
                'materials': ['Bottle caps (various colors)', 'Fraction mats', 'Dry erase markers', 'Problem cards'],
                'game_rules': ['Draw problem card', 'Use bottle caps to model fractions', 'Find common denominator', 'Add or subtract', 'Verify with partner'],
                'key_terms': {'Common Denominator': 'Shared bottom number', 'Unlike Denominators': 'Different bottom numbers', 'LCD': 'Least Common Denominator'},
                'is_published': True,
                'order': 2
            },
            {
                'title': 'Simon Says & Switch',
                'slug': 'simon-says-switch-5',
                'description': 'Active game combining Simon Says with fraction operations and quick thinking.',
                'activity_number': 3,
                'grade': '5',
                'topics': ['Add/Subtract Fractions', 'Multiply/Divide Fractions'],
                'location': 'both',
                'icon_type': 'person',
                'prerequisites': ['All four fraction operations', 'Quick mental math', 'Following directions'],
                'learning_objectives': 'Students will be able to:\n• Perform fraction operations quickly\n• Follow complex directions\n• Self-check calculations',
                'materials': ['Fraction flashcards', 'Answer cards', 'Timer'],
                'game_rules': ['Simon gives fraction command', 'Students solve mentally', 'Move to answer zone', 'Wrong answer sits down', 'Last standing wins'],
                'key_terms': {'Mental Math': 'Solving in your head', 'Operation': 'Add, subtract, multiply, or divide', 'Quick Thinking': 'Fast problem solving'},
                'is_published': True,
                'order': 3
            },
            # GRADE 6
            {
                'title': 'Fraction Multiplication Tag',
                'slug': 'fraction-multiplication-tag-6',
                'description': 'Players solve multiplication problems to tag others and stay in the game.',
                'activity_number': 1,
                'grade': '6',
                'topics': ['Multiply/Divide Fractions'],
                'location': 'court',
                'icon_type': 'multiply',
                'prerequisites': ['Fraction multiplication basics', 'Physical fitness', 'Game strategy'],
                'learning_objectives': 'Students will be able to:\n• Multiply fractions fluently\n• Multiply mixed numbers\n• Simplify products',
                'materials': ['Multiplication cards', 'Pinnies', 'Boundary markers', 'Timer'],
                'game_rules': ['One player is "it"', 'To tag, solve multiplication problem', 'Correct answer = successful tag', 'Tagged player becomes "it"', 'Last untagged wins'],
                'key_terms': {'Product': 'Answer to multiplication', 'Multiply Across': 'Numerator times numerator, denominator times denominator', 'Simplify': 'Reduce to lowest terms'},
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Dividing Fractions Relay',
                'slug': 'dividing-fractions-relay-6',
                'description': 'Teams race to complete fraction division problems using "Keep, Change, Flip."',
                'activity_number': 2,
                'grade': '6',
                'topics': ['Multiply/Divide Fractions'],
                'location': 'court',
                'icon_type': 'divide',
                'prerequisites': ['Multiplication of fractions', 'Understanding reciprocals', 'Team cooperation'],
                'learning_objectives': 'Students will be able to:\n• Divide fractions using reciprocals\n• Apply "Keep, Change, Flip" method\n• Divide mixed numbers',
                'materials': ['Division problem cards', 'Answer key', 'Relay batons', 'Cones'],
                'game_rules': ['Teams line up relay style', 'First player runs to problem station', 'Solve division problem', 'Run back with answer', 'Correct = next player goes'],
                'key_terms': {'Reciprocal': 'Flip the fraction', 'Keep Change Flip': 'Division method', 'Quotient': 'Answer to division'},
                'is_published': True,
                'order': 2
            },
            # GRADE 7
            {
                'title': 'Ratio Basketball',
                'slug': 'ratio-basketball-7',
                'description': 'Apply ratio and proportion concepts while playing basketball challenges.',
                'activity_number': 1,
                'grade': '7',
                'topics': ['Ratio/Proportion'],
                'location': 'court',
                'icon_type': 'ratio',
                'prerequisites': ['Ratio understanding', 'Proportion solving', 'Basketball skills'],
                'learning_objectives': 'Students will be able to:\n• Set up ratios from real situations\n• Solve proportions\n• Apply ratios to sports statistics',
                'materials': ['Basketball', 'Hoops', 'Ratio problem cards', 'Score sheets'],
                'game_rules': ['Attempt baskets in sets', 'Calculate made/attempted ratio', 'Predict next set using proportions', 'Closest prediction wins', 'Track statistics'],
                'key_terms': {'Ratio': 'Comparison of two quantities', 'Proportion': 'Equal ratios', 'Rate': 'Ratio with different units'},
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Decimal Dash',
                'slug': 'decimal-dash-7',
                'description': 'Race through checkpoints by converting between fractions, decimals, and percents.',
                'activity_number': 2,
                'grade': '7',
                'topics': ['Decimals/Percents'],
                'location': 'court',
                'icon_type': 'percent',
                'prerequisites': ['Fraction to decimal conversion', 'Decimal to percent conversion', 'Physical endurance'],
                'learning_objectives': 'Students will be able to:\n• Convert between fractions, decimals, and percents\n• Perform conversions quickly\n• Check conversion accuracy',
                'materials': ['Checkpoint stations', 'Conversion cards', 'Timer', 'Answer sheets'],
                'game_rules': ['Start at first checkpoint', 'Complete conversion correctly', 'Move to next checkpoint', 'Wrong answer = penalty lap', 'Fastest completion wins'],
                'key_terms': {'Decimal': 'Number with decimal point', 'Percent': 'Per hundred', 'Convert': 'Change form'},
                'is_published': True,
                'order': 2
            },
            # GRADE 8
            {
                'title': 'Fraction Expression Challenge',
                'slug': 'fraction-expression-challenge-8',
                'description': 'Solve algebraic expressions with fractions in competitive team challenges.',
                'activity_number': 1,
                'grade': '8',
                'topics': ['Word Problems', 'Add/Subtract Fractions'],
                'location': 'classroom',
                'icon_type': 'algebra',
                'prerequisites': ['All fraction operations', 'Algebraic thinking', 'Order of operations'],
                'learning_objectives': 'Students will be able to:\n• Simplify expressions with fractions\n• Solve equations with fraction coefficients\n• Apply fractions in algebraic contexts',
                'materials': ['Expression cards', 'Whiteboards', 'Markers', 'Timer'],
                'game_rules': ['Teams receive expression', 'Simplify or solve within time limit', 'Show work on whiteboard', 'Correct answers earn points', 'Most points wins'],
                'key_terms': {'Expression': 'Mathematical phrase', 'Coefficient': 'Number multiplied by variable', 'Simplify': 'Reduce to simplest form'},
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Real-World Fraction Olympics',
                'slug': 'real-world-fraction-olympics-8',
                'description': 'Multi-event competition applying fractions to real-world scenarios.',
                'activity_number': 2,
                'grade': '8',
                'topics': ['Word Problems', 'Ratio/Proportion', 'Decimals/Percents'],
                'location': 'both',
                'icon_type': 'trophy',
                'prerequisites': ['All fraction skills', 'Problem-solving strategies', 'Real-world applications'],
                'learning_objectives': 'Students will be able to:\n• Apply fractions to real-world problems\n• Combine multiple fraction skills\n• Explain mathematical reasoning',
                'materials': ['Event station cards', 'Real-world scenarios', 'Calculators (optional)', 'Scoring rubrics'],
                'game_rules': ['Rotate through event stations', 'Solve real-world problem at each', 'Show work and explain reasoning', 'Judges score accuracy and explanation', 'Highest total score wins'],
                'key_terms': {'Application': 'Using math in real situations', 'Reasoning': 'Explaining your thinking', 'Multi-step': 'Problems with several parts'},
                'is_published': True,
                'order': 2
            },
        ]

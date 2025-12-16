"""
Management command to seed activities for V4 interface
"""
from django.core.management.base import BaseCommand
from content.models import Activity
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Seed initial activities for Fraction Ball V4 interface'
    
    def handle(self, *args, **options):
        self.stdout.write('Seeding activities for all grades K-8...')
        
        activities_data = [
            # ===========================================
            # KINDERGARTEN ACTIVITIES
            # ===========================================
            {
                'title': 'Half & Half Hoops',
                'slug': 'half-half-hoops-k',
                'description': 'Kindergartners learn about halves by splitting groups of balls and sharing equally.',
                'activity_number': 1,
                'grade': 'K',
                'topics': ['Fractions Basics', 'Equal Parts'],
                'location': 'court',
                'icon_type': 'ball',
                'prerequisites': [
                    'Counting to 10',
                    'Understanding "same" and "different"',
                    'Basic throwing skills'
                ],
                'learning_objectives': 'Students will be able to:\n• Identify two equal parts (halves)\n• Split a group into two equal parts\n• Use the word "half" correctly',
                'materials': ['Soft balls (10)', 'Two buckets', 'Number cards'],
                'game_rules': [
                    'Teacher shows a group of balls',
                    'Students count the total',
                    'Class splits balls into two equal buckets',
                    'Students practice saying "half"',
                    'Repeat with different amounts'
                ],
                'key_terms': {
                    'Half': 'One of two equal parts',
                    'Equal': 'The same amount',
                    'Whole': 'All of something'
                },
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
                'prerequisites': [
                    'Understanding halves',
                    'Counting to 20',
                    'Fine motor skills'
                ],
                'learning_objectives': 'Students will be able to:\n• Identify four equal parts (quarters)\n• Split items into four groups\n• Compare halves and quarters',
                'materials': ['Play dough', 'Plastic knives', 'Paper circles', 'Crayons'],
                'game_rules': [
                    'Students receive a ball of play dough',
                    'First, split into halves',
                    'Then, split each half again',
                    'Count the four equal pieces',
                    'Color paper circles to show quarters'
                ],
                'key_terms': {
                    'Quarter': 'One of four equal parts',
                    'Fourth': 'Same as a quarter',
                    'Divide': 'To split into parts'
                },
                'is_published': True,
                'order': 2
            },
            
            # ===========================================
            # GRADE 1 ACTIVITIES
            # ===========================================
            {
                'title': 'Pizza Party Fractions',
                'slug': 'pizza-party-fractions-1',
                'description': 'First graders learn fractions by sharing pretend pizzas equally among friends.',
                'activity_number': 1,
                'grade': '1',
                'topics': ['Fractions Basics', 'Equal Parts'],
                'location': 'classroom',
                'icon_type': 'pizza',
                'prerequisites': [
                    'Understanding halves and quarters',
                    'Counting skills',
                    'Sharing concepts'
                ],
                'learning_objectives': 'Students will be able to:\n• Divide shapes into 2, 3, and 4 equal parts\n• Name the parts (halves, thirds, fourths)\n• Understand fair sharing',
                'materials': ['Paper plates', 'Scissors', 'Markers', 'Fraction circles'],
                'game_rules': [
                    'Students create paper "pizzas"',
                    'Fold and cut into equal slices',
                    'Practice sharing with 2, 3, or 4 friends',
                    'Name each piece using fraction words',
                    'Compare sizes of different pieces'
                ],
                'key_terms': {
                    'Third': 'One of three equal parts',
                    'Equal Parts': 'Pieces that are the same size',
                    'Share': 'To divide fairly'
                },
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
                'icon_type': 'person',
                'prerequisites': [
                    'Physical hopping ability',
                    'Shape recognition',
                    'Basic fraction vocabulary'
                ],
                'learning_objectives': 'Students will be able to:\n• Identify fraction names while moving\n• Match shapes to fraction names\n• Build fraction vocabulary through play',
                'materials': ['Chalk or tape', 'Fraction cards', 'Bean bags'],
                'game_rules': [
                    'Create hopscotch with fraction shapes in squares',
                    'Students hop and call out the fraction name',
                    'Toss bean bag to a specific fraction',
                    'Hop to collect it',
                    'First to identify all fractions wins'
                ],
                'key_terms': {
                    'Identify': 'To recognize and name',
                    'Fraction': 'A part of a whole',
                    'Name': 'What we call something'
                },
                'is_published': True,
                'order': 2
            },
            
            # ===========================================
            # GRADE 2 ACTIVITIES
            # ===========================================
            {
                'title': 'Fraction Relay Race',
                'slug': 'fraction-relay-race-2',
                'description': 'Teams race to match fraction pictures with their names and symbols.',
                'activity_number': 1,
                'grade': '2',
                'topics': ['Fractions Basics', 'Fraction Names'],
                'location': 'court',
                'icon_type': 'running',
                'prerequisites': [
                    'Know halves, thirds, and fourths',
                    'Can run safely',
                    'Team work skills'
                ],
                'learning_objectives': 'Students will be able to:\n• Match fraction pictures to symbols (1/2, 1/3, 1/4)\n• Read and write simple fractions\n• Work as a team with fractions',
                'materials': ['Fraction picture cards', 'Fraction symbol cards', 'Cones', 'Baskets'],
                'game_rules': [
                    'Divide class into relay teams',
                    'Pictures at one end, symbols at other',
                    'Runner takes a picture, runs to find matching symbol',
                    'Bring back the pair to the team',
                    'First team with all matches wins'
                ],
                'key_terms': {
                    'Numerator': 'The top number (how many parts you have)',
                    'Denominator': 'The bottom number (total equal parts)',
                    'Fraction Symbol': 'Numbers written as one over another'
                },
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Number Line Jump',
                'slug': 'number-line-jump-2',
                'description': 'Students physically jump to positions on a large number line to find fractions.',
                'activity_number': 2,
                'grade': '2',
                'topics': ['Number Line', 'Fractions Basics'],
                'location': 'both',
                'icon_type': 'number-line',
                'prerequisites': [
                    'Counting by halves',
                    'Understanding 0 and 1',
                    'Physical coordination'
                ],
                'learning_objectives': 'Students will be able to:\n• Place fractions on a number line\n• Understand fractions are between 0 and 1\n• Jump to correct fraction positions',
                'materials': ['Large tape number line', 'Fraction cards', 'Markers'],
                'game_rules': [
                    'Create a large number line from 0 to 1 on the floor',
                    'Divide into halves, then fourths',
                    'Teacher calls out a fraction',
                    'Students jump to that position',
                    'Discuss who is closest to correct spot'
                ],
                'key_terms': {
                    'Number Line': 'A line that shows numbers in order',
                    'Position': 'Where something is located',
                    'Between': 'In the middle of two things'
                },
                'is_published': True,
                'order': 2
            },
            
            # ===========================================
            # GRADE 3 ACTIVITIES
            # ===========================================
            {
                'title': 'Equivalent Fraction Basketball',
                'slug': 'equivalent-fraction-basketball-3',
                'description': 'Students shoot baskets and learn that different fractions can be equal (1/2 = 2/4).',
                'activity_number': 1,
                'grade': '3',
                'topics': ['Equivalent Fractions'],
                'location': 'court',
                'icon_type': 'basketball',
                'prerequisites': [
                    'Basic fraction understanding',
                    'Can shoot a basketball',
                    'Multiplication by 2 and 3'
                ],
                'learning_objectives': 'Students will be able to:\n• Identify equivalent fractions\n• Create equivalent fractions by multiplying\n• Prove two fractions are equal',
                'materials': ['Basketball', 'Hoop', 'Equivalent fraction cards', 'Whiteboard'],
                'game_rules': [
                    'Player draws a fraction card',
                    'Must name an equivalent fraction to shoot',
                    'If correct and makes basket: 2 points',
                    'If correct but misses: 1 point',
                    'If incorrect: explain the right answer'
                ],
                'key_terms': {
                    'Equivalent': 'Equal in value',
                    'Same Value': 'Worth the same amount',
                    'Multiply': 'Make a number bigger by repeated addition'
                },
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Fraction Comparison Toss',
                'slug': 'fraction-comparison-toss-3',
                'description': 'Students compare fractions and toss balls to the greater or lesser side.',
                'activity_number': 2,
                'grade': '3',
                'topics': ['Comparing/Ordering'],
                'location': 'court',
                'icon_type': 'compare',
                'prerequisites': [
                    'Know numerator and denominator',
                    'Understand greater/less than',
                    'Basic equivalent fractions'
                ],
                'learning_objectives': 'Students will be able to:\n• Compare two fractions\n• Determine which fraction is greater\n• Use comparison symbols (<, >, =)',
                'materials': ['Bean bags', 'Two hoops labeled > and <', 'Fraction pair cards'],
                'game_rules': [
                    'Draw a card with two fractions',
                    'Decide which is greater',
                    'Toss bean bag to > or < hoop',
                    'Explain your reasoning',
                    'Points for correct comparisons'
                ],
                'key_terms': {
                    'Greater Than': 'More than another number (>)',
                    'Less Than': 'Smaller than another number (<)',
                    'Compare': 'To look at two things and find differences'
                },
                'is_published': True,
                'order': 2
            },
            
            # ===========================================
            # GRADE 4 ACTIVITIES
            # ===========================================
            {
                'title': 'Adding Fractions Soccer',
                'slug': 'adding-fractions-soccer-4',
                'description': 'Students add fractions with like denominators while playing a modified soccer game.',
                'activity_number': 1,
                'grade': '4',
                'topics': ['Add/Subtract Fractions'],
                'location': 'court',
                'icon_type': 'soccer',
                'prerequisites': [
                    'Adding whole numbers',
                    'Understanding like denominators',
                    'Basic soccer skills'
                ],
                'learning_objectives': 'Students will be able to:\n• Add fractions with like denominators\n• Keep the denominator the same when adding\n• Apply fraction addition in games',
                'materials': ['Soccer ball', 'Cones', 'Fraction addition cards', 'Scoreboard'],
                'game_rules': [
                    'Teams pass the ball and receive fraction cards',
                    'Each pass adds a fraction to team total',
                    'All fractions have same denominator',
                    'Team must track running total',
                    'First to reach target fraction scores a goal'
                ],
                'key_terms': {
                    'Like Denominators': 'Fractions with the same bottom number',
                    'Sum': 'The answer when adding',
                    'Running Total': 'Adding as you go'
                },
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Mixed Number Obstacle Course',
                'slug': 'mixed-number-obstacle-4',
                'description': 'Navigate an obstacle course while converting between mixed numbers and improper fractions.',
                'activity_number': 2,
                'grade': '4',
                'topics': ['Mixed ↔ Improper'],
                'location': 'court',
                'icon_type': 'obstacle',
                'prerequisites': [
                    'Understand mixed numbers',
                    'Understand improper fractions',
                    'Multiplication facts'
                ],
                'learning_objectives': 'Students will be able to:\n• Convert mixed numbers to improper fractions\n• Convert improper fractions to mixed numbers\n• Complete conversions quickly',
                'materials': ['Cones', 'Hurdles', 'Conversion cards', 'Timer'],
                'game_rules': [
                    'Set up obstacle course with stations',
                    'At each station, solve a conversion problem',
                    'Correct answer = proceed to next obstacle',
                    'Wrong answer = do 5 jumping jacks, try again',
                    'Best time through course wins'
                ],
                'key_terms': {
                    'Mixed Number': 'A whole number plus a fraction (2 1/2)',
                    'Improper Fraction': 'Numerator larger than denominator (5/2)',
                    'Convert': 'To change from one form to another'
                },
                'is_published': True,
                'order': 2
            },
            
            # ===========================================
            # GRADE 5 ACTIVITIES (Original)
            # ===========================================
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
                'materials': ['Basketball', 'Cones (at least 10)', 'Court or large open space', 'Fraction cards', 'Scoresheet'],
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
                'materials': ['Bottle caps (various colors)', 'Fraction cards', 'Sorting trays', 'Markers', 'Worksheets'],
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
                'materials': ['Fraction cards (large, visible)', 'Movement space', 'Whistle or bell', 'Score cards', 'Timer'],
                'game_rules': [
                    'Teacher calls out "Simon Says" followed by a fraction operation',
                    'Students must physically represent the answer',
                    'When "Switch" is called, students switch problems with a partner',
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
            
            # ===========================================
            # GRADE 6 ACTIVITIES
            # ===========================================
            {
                'title': 'Fraction Multiplication Tag',
                'slug': 'fraction-multiplication-tag-6',
                'description': 'Students play tag while solving fraction multiplication problems to free teammates.',
                'activity_number': 1,
                'grade': '6',
                'topics': ['Multiply/Divide Fractions (6+)'],
                'location': 'court',
                'icon_type': 'multiply',
                'prerequisites': [
                    'Multiplying whole numbers',
                    'Understanding numerator × numerator',
                    'Running safely'
                ],
                'learning_objectives': 'Students will be able to:\n• Multiply fractions by fractions\n• Multiply fractions by whole numbers\n• Simplify products',
                'materials': ['Pinnies for taggers', 'Multiplication cards', 'Boundary cones', 'Answer key'],
                'game_rules': [
                    '2-3 taggers try to tag runners',
                    'Tagged players go to "fraction jail"',
                    'To free a teammate, solve a multiplication problem',
                    'Correct answer releases the player',
                    'Switch taggers every 3 minutes'
                ],
                'key_terms': {
                    'Multiply Fractions': 'Numerator × numerator, denominator × denominator',
                    'Product': 'The answer to a multiplication problem',
                    'Simplify': 'Reduce to lowest terms'
                },
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Dividing Fractions Relay',
                'slug': 'dividing-fractions-relay-6',
                'description': 'Teams race to solve fraction division problems using the "flip and multiply" method.',
                'activity_number': 2,
                'grade': '6',
                'topics': ['Multiply/Divide Fractions (6+)'],
                'location': 'court',
                'icon_type': 'divide',
                'prerequisites': [
                    'Multiplying fractions',
                    'Understanding reciprocals',
                    'Team relay experience'
                ],
                'learning_objectives': 'Students will be able to:\n• Find the reciprocal of a fraction\n• Divide fractions using "flip and multiply"\n• Check answers for reasonableness',
                'materials': ['Division problem cards', 'Whiteboards', 'Markers', 'Relay batons'],
                'game_rules': [
                    'Teams line up in relay formation',
                    'First runner gets a division problem',
                    'Solve by flipping and multiplying',
                    'Write answer on team whiteboard',
                    'Pass baton to next runner',
                    'First team with all correct answers wins'
                ],
                'key_terms': {
                    'Reciprocal': 'A fraction flipped upside down (2/3 → 3/2)',
                    'Flip and Multiply': 'Divide by multiplying by the reciprocal',
                    'Quotient': 'The answer to a division problem'
                },
                'is_published': True,
                'order': 2
            },
            
            # ===========================================
            # GRADE 7 ACTIVITIES
            # ===========================================
            {
                'title': 'Ratio Basketball',
                'slug': 'ratio-basketball-7',
                'description': 'Students explore ratios and proportions through basketball shooting statistics.',
                'activity_number': 1,
                'grade': '7',
                'topics': ['Ratio/Proportion (6+)'],
                'location': 'court',
                'icon_type': 'ratio',
                'prerequisites': [
                    'Basic fraction operations',
                    'Understanding ratios',
                    'Basketball shooting'
                ],
                'learning_objectives': 'Students will be able to:\n• Write ratios from real data\n• Find equivalent ratios\n• Set up and solve proportions',
                'materials': ['Basketballs', 'Scoring sheets', 'Calculators', 'Ratio problem cards'],
                'game_rules': [
                    'Each student takes 10 shots',
                    'Record makes and misses',
                    'Write the ratio of makes to total shots',
                    'Calculate what their makes would be out of 100',
                    'Compare shooting percentages using proportions'
                ],
                'key_terms': {
                    'Ratio': 'A comparison of two quantities',
                    'Proportion': 'An equation showing two ratios are equal',
                    'Shooting Percentage': 'Makes divided by attempts, times 100'
                },
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Decimal Dash',
                'slug': 'decimal-dash-7',
                'description': 'Students convert between fractions, decimals, and percents in a racing format.',
                'activity_number': 2,
                'grade': '7',
                'topics': ['Decimals & Percents'],
                'location': 'both',
                'icon_type': 'percent',
                'prerequisites': [
                    'Fraction operations',
                    'Basic decimal understanding',
                    'Division skills'
                ],
                'learning_objectives': 'Students will be able to:\n• Convert fractions to decimals\n• Convert decimals to percents\n• Move fluently between representations',
                'materials': ['Conversion cards', 'Running track or cones', 'Answer stations', 'Timers'],
                'game_rules': [
                    'Three stations: Fraction, Decimal, Percent',
                    'Start with a number at any station',
                    'Convert and run to the matching representation',
                    'Verify answer at station',
                    'Continue until all conversions complete'
                ],
                'key_terms': {
                    'Decimal': 'A number written with a decimal point',
                    'Percent': 'Per hundred (out of 100)',
                    'Convert': 'Change from one form to another'
                },
                'is_published': True,
                'order': 2
            },
            
            # ===========================================
            # GRADE 8 ACTIVITIES
            # ===========================================
            {
                'title': 'Fraction Expression Challenge',
                'slug': 'fraction-expression-challenge-8',
                'description': 'Students simplify algebraic expressions with fractions in a competitive team format.',
                'activity_number': 1,
                'grade': '8',
                'topics': ['Word Problems', 'Add/Subtract Fractions'],
                'location': 'classroom',
                'icon_type': 'algebra',
                'prerequisites': [
                    'All fraction operations',
                    'Basic algebra understanding',
                    'Variable expressions'
                ],
                'learning_objectives': 'Students will be able to:\n• Add and subtract algebraic fractions\n• Find common denominators with variables\n• Simplify complex fraction expressions',
                'materials': ['Expression cards', 'Whiteboards', 'Markers', 'Timer', 'Answer key'],
                'game_rules': [
                    'Teams receive algebraic fraction expressions',
                    'Simplify or combine the expressions',
                    'First team with correct simplified form earns points',
                    'Bonus points for showing all steps',
                    'Tournament-style bracket for finals'
                ],
                'key_terms': {
                    'Algebraic Fraction': 'A fraction containing variables',
                    'Like Terms': 'Terms with the same variables',
                    'Simplify': 'Combine and reduce to simplest form'
                },
                'is_published': True,
                'order': 1
            },
            {
                'title': 'Real-World Fraction Olympics',
                'slug': 'real-world-fraction-olympics-8',
                'description': 'Students apply all fraction skills to solve real-world problems in an Olympic competition format.',
                'activity_number': 2,
                'grade': '8',
                'topics': ['Word Problems', 'Ratio/Proportion (6+)', 'Decimals & Percents'],
                'location': 'both',
                'icon_type': 'trophy',
                'prerequisites': [
                    'All fraction operations',
                    'Ratios and proportions',
                    'Percent applications'
                ],
                'learning_objectives': 'Students will be able to:\n• Apply fractions to real-world contexts\n• Solve multi-step word problems\n• Choose appropriate operations',
                'materials': ['Word problem cards by category', 'Calculators', 'Recording sheets', 'Medal awards'],
                'game_rules': [
                    'Events: Recipe Scaling, Discount Shopping, Sports Stats, Construction Plans',
                    'Students compete in each "event"',
                    'Solve real-world problems using fractions',
                    'Points based on accuracy and speed',
                    'Medal ceremony for top performers'
                ],
                'key_terms': {
                    'Application': 'Using math in real situations',
                    'Multi-step': 'Problems requiring several calculations',
                    'Context': 'The real-world situation in a problem'
                },
                'is_published': True,
                'order': 2
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
                    self.style.SUCCESS(f'✓ Created: {activity.title} (Grade {activity.grade})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated: {activity.title} (Grade {activity.grade})')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_count} new activities and updated {updated_count} existing activities!'
            )
        )
        
        # Summary by grade
        from django.db.models import Count
        grade_counts = Activity.objects.values('grade').annotate(count=Count('id')).order_by('grade')
        self.stdout.write('')
        self.stdout.write('📊 Activities by Grade:')
        for gc in grade_counts:
            grade_display = 'Kindergarten' if gc['grade'] == 'K' else f"Grade {gc['grade']}"
            self.stdout.write(f"   {grade_display}: {gc['count']} activities")

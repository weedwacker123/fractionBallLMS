"""
Management command to seed Firestore with CMS data:
- Taxonomies (grades, topics, court types)
- Menu items (header/footer navigation)
- Site configuration values
"""
from django.core.management.base import BaseCommand
from datetime import datetime


def get_firestore_client():
    """Get Firestore client with explicit database name and credentials"""
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


class Command(BaseCommand):
    help = 'Seed Firestore with CMS data: taxonomies, menus, site config, and FAQs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )
        parser.add_argument(
            '--only',
            choices=['taxonomies', 'menus', 'config', 'faqs', 'all'],
            default='all',
            help='Seed only specific data type',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        clear = options.get('clear', False)
        only = options.get('only', 'all')

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No data will be written'))

        db = get_firestore_client()

        if only in ['all', 'taxonomies']:
            self.seed_taxonomies(db, clear, dry_run)

        if only in ['all', 'menus']:
            self.seed_menu_items(db, clear, dry_run)

        if only in ['all', 'config']:
            self.seed_site_config(db, clear, dry_run)

        if only in ['all', 'faqs']:
            self.seed_faqs(db, clear, dry_run)

        self.stdout.write(self.style.SUCCESS('Seeding complete!'))

    def seed_taxonomies(self, db, clear, dry_run):
        """Seed taxonomy data (grades, topics, court types)"""
        self.stdout.write('\nSeeding taxonomies...')
        collection_name = 'taxonomies'

        if clear and not dry_run:
            self.clear_collection(db, collection_name)

        taxonomies = self.get_taxonomy_data()
        created = 0

        for taxonomy in taxonomies:
            if dry_run:
                self.stdout.write(f"  Would create: {taxonomy['type']} - {taxonomy['name']}")
            else:
                doc_ref = db.collection(collection_name).document()
                taxonomy['createdAt'] = datetime.utcnow()
                taxonomy['updatedAt'] = datetime.utcnow()
                doc_ref.set(taxonomy)
                self.stdout.write(f"  Created: {taxonomy['type']} - {taxonomy['name']}")
            created += 1

        self.stdout.write(self.style.SUCCESS(f'  Taxonomies: {created} items'))

    def seed_menu_items(self, db, clear, dry_run):
        """Seed menu items for header and footer navigation"""
        self.stdout.write('\nSeeding menu items...')
        collection_name = 'menuItems'

        if clear and not dry_run:
            self.clear_collection(db, collection_name)

        menu_items = self.get_menu_data()
        created = 0

        for item in menu_items:
            if dry_run:
                self.stdout.write(f"  Would create: [{item['location']}] {item['label']}")
            else:
                doc_ref = db.collection(collection_name).document()
                item['createdAt'] = datetime.utcnow()
                item['updatedAt'] = datetime.utcnow()
                doc_ref.set(item)
                self.stdout.write(f"  Created: [{item['location']}] {item['label']}")
            created += 1

        self.stdout.write(self.style.SUCCESS(f'  Menu items: {created} items'))

    def seed_site_config(self, db, clear, dry_run):
        """Seed site configuration values"""
        self.stdout.write('\nSeeding site configuration...')
        collection_name = 'siteConfig'

        if clear and not dry_run:
            self.clear_collection(db, collection_name)

        configs = self.get_site_config_data()
        created = 0

        for config in configs:
            if dry_run:
                self.stdout.write(f"  Would create: {config['key']} = {config['value']}")
            else:
                doc_ref = db.collection(collection_name).document()
                config['updatedAt'] = datetime.utcnow()
                doc_ref.set(config)
                self.stdout.write(f"  Created: {config['key']}")
            created += 1

        self.stdout.write(self.style.SUCCESS(f'  Site config: {created} items'))

    def seed_faqs(self, db, clear, dry_run):
        """Seed FAQ entries"""
        self.stdout.write('\nSeeding FAQs...')
        collection_name = 'faqs'

        if clear and not dry_run:
            self.clear_collection(db, collection_name)

        faqs = self.get_faq_data()
        created = 0

        for faq in faqs:
            if dry_run:
                self.stdout.write(f"  Would create: [{faq['category']}] {faq['question'][:50]}...")
            else:
                doc_ref = db.collection(collection_name).document()
                faq['createdAt'] = datetime.utcnow()
                faq['updatedAt'] = datetime.utcnow()
                doc_ref.set(faq)
                self.stdout.write(f"  Created: [{faq['category']}] {faq['question'][:50]}...")
            created += 1

        self.stdout.write(self.style.SUCCESS(f'  FAQs: {created} items'))

    def clear_collection(self, db, collection_name):
        """Clear all documents in a collection"""
        self.stdout.write(f'  Clearing {collection_name}...')
        docs = db.collection(collection_name).stream()
        count = 0
        for doc in docs:
            doc.reference.delete()
            count += 1
        self.stdout.write(f'  Cleared {count} documents')

    def get_taxonomy_data(self):
        """Return taxonomy seed data - grouped structure with values[] array"""
        return [
            # Grade Levels (single document with all grades)
            {
                'name': 'Grade Levels',
                'type': 'grade',
                'active': True,
                'displayOrder': 1,
                'hierarchical': False,
                'values': [
                    {'key': 'K', 'label': 'Kindergarten'},
                    {'key': '1', 'label': 'Grade 1'},
                    {'key': '2', 'label': 'Grade 2'},
                    {'key': '3', 'label': 'Grade 3'},
                    {'key': '4', 'label': 'Grade 4'},
                    {'key': '5', 'label': 'Grade 5'},
                    {'key': '6', 'label': 'Grade 6'},
                    {'key': '7', 'label': 'Grade 7'},
                    {'key': '8', 'label': 'Grade 8'},
                ]
            },
            # Math Topics (single document with all topics)
            {
                'name': 'Math Topics',
                'type': 'topic',
                'active': True,
                'displayOrder': 2,
                'hierarchical': False,
                'values': [
                    {'key': 'fractions_basics', 'label': 'Fractions Basics', 'description': 'Introduction to fractions'},
                    {'key': 'equivalent_fractions', 'label': 'Equivalent Fractions', 'description': 'Finding equal fractions'},
                    {'key': 'comparing_ordering', 'label': 'Comparing/Ordering', 'description': 'Comparing fraction sizes'},
                    {'key': 'add_subtract', 'label': 'Add/Subtract Fractions', 'description': 'Adding and subtracting fractions'},
                    {'key': 'multiply_divide', 'label': 'Multiply/Divide Fractions', 'description': 'Multiplying and dividing fractions'},
                    {'key': 'mixed_improper', 'label': 'Mixed/Improper', 'description': 'Converting between mixed and improper'},
                    {'key': 'decimals_percents', 'label': 'Decimals/Percents', 'description': 'Fractions to decimals and percents'},
                    {'key': 'word_problems', 'label': 'Word Problems', 'description': 'Real-world fraction problems'},
                    {'key': 'number_line', 'label': 'Number Line', 'description': 'Fractions on a number line'},
                    {'key': 'ratio_proportion', 'label': 'Ratio/Proportion', 'description': 'Ratios and proportions'},
                    {'key': 'equal_parts', 'label': 'Equal Parts', 'description': 'Dividing wholes into equal parts'},
                ]
            },
            # Court Types (single document with all court types)
            {
                'name': 'Court Types',
                'type': 'court',
                'active': True,
                'displayOrder': 3,
                'hierarchical': False,
                'values': [
                    {'key': 'classroom', 'label': 'Classroom', 'description': 'Indoor classroom activities'},
                    {'key': 'court', 'label': 'Basketball Court', 'description': 'Court or gym activities'},
                    {'key': 'both', 'label': 'Both', 'description': 'Can be done in classroom or on court'},
                    {'key': 'field', 'label': 'Outdoor Field', 'description': 'Outdoor field activities'},
                ]
            },
        ]

    def get_menu_data(self):
        """Return menu items seed data"""
        return [
            # Header menu items
            {
                'label': 'Activities',
                'url': '/activities/',
                'location': 'header',
                'type': 'page',
                'displayOrder': 1,
                'active': True,
                'openInNewTab': False,
                'parentId': None,
            },
            {
                'label': 'Community',
                'url': '/community/',
                'location': 'header',
                'type': 'page',
                'displayOrder': 2,
                'active': True,
                'openInNewTab': False,
                'parentId': None,
            },
            {
                'label': 'FAQs',
                'url': '/faqs/',
                'location': 'header',
                'type': 'page',
                'displayOrder': 3,
                'active': True,
                'openInNewTab': False,
                'parentId': None,
            },
            {
                'label': 'About',
                'url': '/page/about/',
                'location': 'header',
                'type': 'page',
                'displayOrder': 4,
                'active': True,
                'openInNewTab': False,
                'parentId': None,
            },

            # Footer menu items
            {
                'label': 'Privacy Policy',
                'url': '/page/privacy/',
                'location': 'footer',
                'type': 'page',
                'displayOrder': 1,
                'active': True,
                'openInNewTab': False,
                'parentId': None,
            },
            {
                'label': 'Terms of Service',
                'url': '/page/terms/',
                'location': 'footer',
                'type': 'page',
                'displayOrder': 2,
                'active': True,
                'openInNewTab': False,
                'parentId': None,
            },
            {
                'label': 'Contact',
                'url': '/page/contact/',
                'location': 'footer',
                'type': 'page',
                'displayOrder': 3,
                'active': True,
                'openInNewTab': False,
                'parentId': None,
            },
            {
                'label': 'Help',
                'url': '/faqs/',
                'location': 'footer',
                'type': 'page',
                'displayOrder': 4,
                'active': True,
                'openInNewTab': False,
                'parentId': None,
            },
        ]

    def get_site_config_data(self):
        """Return site configuration seed data"""
        return [
            {
                'key': 'site_name',
                'value': 'Fraction Ball',
                'description': 'The name of the site displayed in header and footer',
                'dataType': 'string',
            },
            {
                'key': 'site_tagline',
                'value': 'Making Math Fun Through Sports',
                'description': 'Site tagline/slogan',
                'dataType': 'string',
            },
            {
                'key': 'max_video_size',
                'value': 524288000,  # 500MB in bytes
                'description': 'Maximum video upload size in bytes',
                'dataType': 'number',
            },
            {
                'key': 'max_resource_size',
                'value': 52428800,  # 50MB in bytes
                'description': 'Maximum resource/document upload size in bytes',
                'dataType': 'number',
            },
            {
                'key': 'allowed_video_types',
                'value': ['video/mp4', 'video/mpeg', 'video/quicktime', 'video/x-msvideo', 'video/webm'],
                'description': 'Allowed MIME types for video uploads',
                'dataType': 'array',
            },
            {
                'key': 'allowed_resource_types',
                'value': [
                    'application/pdf',
                    'application/msword',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                    'application/vnd.ms-powerpoint',
                    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                    'application/vnd.ms-excel',
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'text/plain',
                    'image/jpeg',
                    'image/png',
                    'image/gif'
                ],
                'description': 'Allowed MIME types for resource uploads',
                'dataType': 'array',
            },
            {
                'key': 'items_per_page',
                'value': 12,
                'description': 'Default number of items per page in listings',
                'dataType': 'number',
            },
            {
                'key': 'enable_community',
                'value': True,
                'description': 'Enable or disable the community features',
                'dataType': 'boolean',
            },
            {
                'key': 'contact_email',
                'value': 'hello@fractionball.com',
                'description': 'Contact email displayed on the site',
                'dataType': 'string',
            },
        ]

    def get_faq_data(self):
        """Return FAQ seed data matching CMS faqs collection schema"""
        return [
            # Getting Started
            {
                'question': 'What is Fraction Ball?',
                'answer': 'Fraction Ball is an innovative math education program that combines physical activity with fraction learning. Students engage in basketball-based activities designed to reinforce fraction concepts through movement and teamwork.',
                'category': 'getting_started',
                'displayOrder': 1,
                'status': 'published',
            },
            {
                'question': 'What grade levels is Fraction Ball designed for?',
                'answer': 'Fraction Ball activities are primarily designed for grades 3-8, with most content focused on grades 4-6. Activities can be adapted for different skill levels within this range.',
                'category': 'getting_started',
                'displayOrder': 2,
                'status': 'published',
            },
            {
                'question': 'What equipment do I need?',
                'answer': 'Basic equipment includes: basketballs (4-6), cones, timer, whistle (optional), and clipboard. Specific activities may require additional items like bottle caps or hula hoops. Each activity page lists the exact materials needed.',
                'category': 'getting_started',
                'displayOrder': 3,
                'status': 'published',
            },
            # Implementation
            {
                'question': 'How long does each activity take?',
                'answer': 'Most activities are designed to fit within a 30-45 minute class period, including setup, instruction, activity time, and wrap-up. Some activities have multiple parts that can be spread across several sessions.',
                'category': 'implementation',
                'displayOrder': 1,
                'status': 'published',
            },
            {
                'question': 'Can I do these activities in a classroom?',
                'answer': 'While Fraction Ball is designed for gym or outdoor court use, some activities have classroom adaptations. Look for the "CLASSROOM" filter to find activities suitable for indoor spaces with limited equipment.',
                'category': 'implementation',
                'displayOrder': 2,
                'status': 'published',
            },
            {
                'question': 'How do I assess student learning?',
                'answer': 'Many activities include running records, observation sheets, and reflection questions. You can assess both math understanding and collaboration skills. Downloadable assessment tools are available in the Resources section of each activity.',
                'category': 'implementation',
                'displayOrder': 3,
                'status': 'published',
            },
            # Technical Support
            {
                'question': 'How do I download resources?',
                'answer': 'Navigate to any activity page and look for the Resources sidebar on the right. Click on any resource to download PDFs, Excel files, or other materials directly to your device.',
                'category': 'technical',
                'displayOrder': 1,
                'status': 'published',
            },
            {
                'question': 'Can I share activities with other teachers?',
                'answer': 'Yes! All activities and resources within your school or district account can be shared. Use the Community features to collaborate and share adaptations with other educators.',
                'category': 'technical',
                'displayOrder': 2,
                'status': 'published',
            },
            {
                'question': 'Who do I contact for technical support?',
                'answer': 'For technical support, please contact support@fractionball.com or use the help button in the bottom right corner of any page. Our support team typically responds within 24 hours.',
                'category': 'technical',
                'displayOrder': 3,
                'status': 'published',
            },
        ]

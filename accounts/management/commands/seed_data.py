from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import School
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with initial data for development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--schools',
            type=int,
            default=3,
            help='Number of schools to create'
        )
        parser.add_argument(
            '--users-per-school',
            type=int,
            default=10,
            help='Number of users per school'
        )

    def handle(self, *args, **options):
        schools_count = options['schools']
        users_per_school = options['users_per_school']

        self.stdout.write('Seeding database with initial data...')

        # Create schools
        schools = []
        school_names = [
            'Lincoln Elementary School',
            'Washington Middle School', 
            'Roosevelt High School',
            'Jefferson Academy',
            'Madison Public School',
            'Adams Charter School'
        ]

        for i in range(schools_count):
            school_name = school_names[i % len(school_names)]
            domain = f"school{i+1}"
            
            school, created = School.objects.get_or_create(
                domain=domain,
                defaults={
                    'name': f"{school_name} {i+1}" if i >= len(school_names) else school_name,
                    'address': f"{100 + i} School Street, Education City, EC 1234{i}",
                    'phone': f"555-{1000 + i:04d}",
                }
            )
            
            if created:
                self.stdout.write(f'Created school: {school.name}')
            else:
                self.stdout.write(f'School already exists: {school.name}')
            
            schools.append(school)

        # Create system admin (if not exists)
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@fractionball.com',
                'first_name': 'System',
                'last_name': 'Admin',
                'role': User.Role.ADMIN,
                'school': schools[0],
                'firebase_uid': 'admin_firebase_uid',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write('Created system admin user (username: admin, password: admin123)')
        else:
            self.stdout.write('System admin already exists')

        # Create users for each school
        first_names = ['Alice', 'Bob', 'Carol', 'David', 'Emma', 'Frank', 'Grace', 'Henry', 'Ivy', 'Jack']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']

        for school in schools:
            # Create school admin
            school_admin_username = f"admin_{school.domain}"
            school_admin, created = User.objects.get_or_create(
                username=school_admin_username,
                defaults={
                    'email': f'admin@{school.domain}.edu',
                    'first_name': 'School',
                    'last_name': 'Admin',
                    'role': User.Role.SCHOOL_ADMIN,
                    'school': school,
                    'firebase_uid': f'school_admin_{school.domain}_firebase_uid',
                    'phone': f'555-{random.randint(1000, 9999)}',
                }
            )
            
            if created:
                school_admin.set_password('admin123')
                school_admin.save()
                self.stdout.write(f'Created school admin for {school.name}: {school_admin_username}')

            # Create teachers
            for i in range(users_per_school - 1):  # -1 because we already created school admin
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                username = f"{first_name.lower()}.{last_name.lower()}.{school.domain}.{i+1}"
                
                teacher, created = User.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f'{first_name.lower()}.{last_name.lower()}@{school.domain}.edu',
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': User.Role.TEACHER,
                        'school': school,
                        'firebase_uid': f'teacher_{username}_firebase_uid',
                        'phone': f'555-{random.randint(1000, 9999)}',
                    }
                )
                
                if created:
                    teacher.set_password('teacher123')
                    teacher.save()

            self.stdout.write(f'Created {users_per_school} users for {school.name}')

        # Summary
        total_schools = School.objects.count()
        total_users = User.objects.count()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nSeeding completed!\n'
                f'Total Schools: {total_schools}\n'
                f'Total Users: {total_users}\n'
                f'System Admin: admin / admin123\n'
                f'School Admins: admin_school1 / admin123, etc.\n'
                f'Teachers: [firstname].[lastname].school1.1 / teacher123, etc.'
            )
        )

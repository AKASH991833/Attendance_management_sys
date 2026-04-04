"""
Management command to create a super admin user.
Usage: python manage.py createsuperadmin
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.accounts.models import Teacher


class Command(BaseCommand):
    help = 'Create a super admin user'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('\n=== EduTrack Pro - Create Super Admin ===\n'))

        # Get username
        username = input('Username (default: superadmin): ').strip() or 'superadmin'

        # Check if user exists
        if User.objects.filter(username=username).exists():
            user = User.objects.get(username=username)
            self.stdout.write(self.style.WARNING(f'\nUser "{username}" already exists.'))

            # Make super admin
            if hasattr(user, 'teacher'):
                user.teacher.is_super_admin = True
                user.teacher.save()
            user.is_staff = True
            user.is_superuser = True
            user.save()

            self.stdout.write(self.style.SUCCESS(f'✓ User "{username}" is now a super admin!'))
            self.stdout.write(self.style.SUCCESS(f'  Login at: http://127.0.0.1:8000/login/\n'))
            return

        # Get other details
        email = input('Email (default: admin@edutrack.com): ').strip() or 'admin@edutrack.com'
        full_name = input('Full Name (default: Super Admin): ').strip() or 'Super Admin'

        # Get password
        while True:
            password = input('Password (default: admin123): ').strip() or 'admin123'
            confirm_password = input('Confirm Password: ').strip() or 'admin123'

            if password == confirm_password:
                break
            else:
                self.stdout.write(self.style.ERROR('Passwords do not match! Please try again.\n'))

        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=full_name.split()[0] if ' ' in full_name else full_name,
            last_name=' '.join(full_name.split()[1:]) if ' ' in full_name else '',
            is_staff=True,
            is_superuser=True
        )

        # Create teacher profile
        teacher = Teacher.objects.get(user=user)
        teacher.full_name = full_name
        teacher.is_super_admin = True
        teacher.department = 'Administration'
        teacher.save()

        self.stdout.write(self.style.SUCCESS('\n✓ Super Admin created successfully!'))
        self.stdout.write(self.style.SUCCESS(f'\n  Username: {username}'))
        self.stdout.write(self.style.SUCCESS(f'  Password: {password}'))
        self.stdout.write(self.style.SUCCESS(f'  Login at: http://127.0.0.1:8000/login/\n'))
        self.stdout.write(self.style.SUCCESS('=== You can now access the Admin Dashboard! ===\n'))

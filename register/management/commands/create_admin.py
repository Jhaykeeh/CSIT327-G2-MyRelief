from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Create a superuser if one does not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get admin credentials from environment variables or use defaults
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        admin_firstname = os.environ.get('ADMIN_FIRSTNAME', 'Admin')
        admin_lastname = os.environ.get('ADMIN_LASTNAME', 'User')
        
        # Check if superuser already exists
        if User.objects.filter(username=admin_username).exists():
            self.stdout.write(
                self.style.WARNING(f'Admin user "{admin_username}" already exists.')
            )
        else:
            # Create superuser
            User.objects.create_superuser(
                username=admin_username,
                email=admin_email,
                password=admin_password,
                firstname=admin_firstname,
                lastname=admin_lastname
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created admin user "{admin_username}"')
            )
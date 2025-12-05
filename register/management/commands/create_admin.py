from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Create a superuser with credentials from environment variables'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get admin credentials from environment variables
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_firstname = os.environ.get('ADMIN_FIRSTNAME', 'Admin')
        admin_lastname = os.environ.get('ADMIN_LASTNAME', 'User')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        # Check if superuser already exists
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                firstname=admin_firstname,
                lastname=admin_lastname,
                password=admin_password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser "{admin_username}"')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Superuser "{admin_username}" already exists')
            )
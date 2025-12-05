from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Create a superuser with credentials from environment variables or defaults'

    def handle(self, *args, **options):
        User = get_user_model()
        
        # Get admin credentials from environment variables or use defaults
        admin_username = os.environ.get('ADMIN_USERNAME', 'JuddAdmin')
        admin_firstname = os.environ.get('ADMIN_FIRSTNAME', 'Judd')
        admin_lastname = os.environ.get('ADMIN_LASTNAME', 'Admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'march242005')
        admin_address = os.environ.get('ADMIN_ADDRESS', 'Admin Office')
        admin_contact = os.environ.get('ADMIN_CONTACT', '00000000000')
        admin_city = os.environ.get('ADMIN_CITY', 'Unknown')
        admin_barangay = os.environ.get('ADMIN_BARANGAY', 'Unknown')
        
        # Check if superuser already exists
        if not User.objects.filter(username=admin_username).exists():
            User.objects.create_superuser(
                username=admin_username,
                firstname=admin_firstname,
                lastname=admin_lastname,
                password=admin_password,
                address=admin_address,
                contact=admin_contact,
                city=admin_city,
                barangay=admin_barangay
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser "{admin_username}"')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'Superuser "{admin_username}" already exists')
            )
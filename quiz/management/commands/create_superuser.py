"""
Django management command to create the default superuser
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from quiz.models import UserProfile


class Command(BaseCommand):
    help = 'Create the default superuser if it does not exist'

    def handle(self, *args, **options):
        username = 'username'
        email = 'emailid'
        password = 'password'
        
        # Check if user already exists
        if User.objects.filter(username=username).exists():
            self.stdout.write(
                self.style.WARNING(f'User "{username}" already exists. Skipping creation.')
            )
            return
        
        # Create superuser
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        # Create user profile with admin role
        UserProfile.objects.create(
            user=user,
            role='admin'
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created superuser "{username}"')
        )

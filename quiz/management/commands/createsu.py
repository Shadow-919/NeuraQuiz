from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Create a default superuser if not exists"

    def handle(self, *args, **kwargs):
        User = get_user_model()

        username = "Shadow"       # 👈 change this
        email = "test46ge8g4@gmail.com" # 👈 change this
        password = "Qwerty123"    # 👈 change this

        if not User.objects.filter(username=username).exists():
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully!"))
        else:
            self.stdout.write(self.style.WARNING(f"Superuser '{username}' already exists."))

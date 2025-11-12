from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os


class Command(BaseCommand):
    help = 'Create or update admin user from environment variables: ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('ADMIN_USERNAME') or os.environ.get('APP_USERNAME')
        email = os.environ.get('ADMIN_EMAIL') or os.environ.get('APP_EMAIL')
        password = os.environ.get('ADMIN_PASSWORD') or os.environ.get('APP_PASSWORD')

        if not username or not password:
            self.stderr.write(self.style.ERROR('ADMIN_USERNAME and ADMIN_PASSWORD environment variables are required'))
            return

        user, created = User.objects.update_or_create(
            username=username,
            defaults={'email': email or '', 'is_staff': True, 'is_superuser': True}
        )
        user.set_password(password)
        user.save()

        if created:
            self.stdout.write(self.style.SUCCESS(f'Created superuser {username}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated superuser {username}'))

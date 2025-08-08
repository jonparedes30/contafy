from django.core.management.base import BaseCommand
from empresa.models import Usuario

class Command(BaseCommand):
    help = 'Resetea la contraseña de un usuario'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username del usuario')
        parser.add_argument('password', type=str, help='Nueva contraseña')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        
        try:
            user = Usuario.objects.get(username=username)
            user.set_password(password)
            user.save()
            self.stdout.write(f"Contraseña actualizada para {username}")
        except Usuario.DoesNotExist:
            self.stdout.write(f"Usuario {username} no existe")
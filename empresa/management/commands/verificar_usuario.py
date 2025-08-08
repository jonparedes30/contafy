from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate
from empresa.models import Usuario

class Command(BaseCommand):
    help = 'Verifica un usuario específico'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username a verificar')
        parser.add_argument('password', type=str, help='Password a verificar')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        
        try:
            user = Usuario.objects.get(username=username)
            self.stdout.write(f"Usuario encontrado: {user.username}")
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"Activo: {user.is_active}")
            self.stdout.write(f"Empresa: {user.empresa}")
            self.stdout.write(f"Password válido: {user.check_password(password)}")
            
            # Probar autenticación
            auth_user = authenticate(username=username, password=password)
            self.stdout.write(f"Autenticación: {'Exitosa' if auth_user else 'Fallida'}")
            
        except Usuario.DoesNotExist:
            self.stdout.write(f"Usuario {username} no existe")
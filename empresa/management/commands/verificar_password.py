from django.core.management.base import BaseCommand
from empresa.models import Usuario

class Command(BaseCommand):
    help = 'Verifica y arregla contraseñas de usuarios'

    def add_arguments(self, parser):
        parser.add_argument('--fix', action='store_true', help='Arreglar contraseñas no hasheadas')

    def handle(self, *args, **options):
        usuarios = Usuario.objects.all()
        
        for user in usuarios:
            password_ok = user.password.startswith('pbkdf2_')
            self.stdout.write(f"Usuario: {user.username}")
            self.stdout.write(f"  Password hasheada: {'Sí' if password_ok else 'NO'}")
            self.stdout.write(f"  Activo: {user.is_active}")
            self.stdout.write(f"  Empresa: {user.empresa}")
            
            if not password_ok and options['fix']:
                # Establecer contraseña por defecto
                user.set_password('123456')
                user.save()
                self.stdout.write(f"  ✓ Password arreglada (nueva: 123456)")
            
            self.stdout.write("---")
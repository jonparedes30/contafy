from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from empresa.models import Empresa

class Command(BaseCommand):
    help = 'Lista todos los usuarios registrados y sus empresas'

    def handle(self, *args, **options):
        self.stdout.write("=== USUARIOS REGISTRADOS ===")
        
        users = User.objects.all().order_by('-date_joined')
        
        for user in users:
            self.stdout.write(f"ID: {user.id}")
            self.stdout.write(f"Usuario: {user.username}")
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"Activo: {user.is_active}")
            self.stdout.write(f"Staff: {user.is_staff}")
            self.stdout.write(f"Superuser: {user.is_superuser}")
            self.stdout.write(f"Fecha registro: {user.date_joined}")
            self.stdout.write(f"Último login: {user.last_login}")
            
            # Buscar empresa asociada
            try:
                empresa = Empresa.objects.get(usuario=user)
                self.stdout.write(f"Empresa: {empresa.nombre} ({empresa.categoria})")
            except Empresa.DoesNotExist:
                self.stdout.write("Empresa: NO TIENE EMPRESA ASOCIADA")
            
            self.stdout.write("---")
        
        self.stdout.write(f"\nTotal usuarios: {users.count()}")
        
        # Mostrar empresas sin usuario
        empresas_sin_usuario = Empresa.objects.filter(usuario__isnull=True)
        if empresas_sin_usuario.exists():
            self.stdout.write("\n=== EMPRESAS SIN USUARIO ===")
            for empresa in empresas_sin_usuario:
                self.stdout.write(f"ID: {empresa.id} - {empresa.nombre}")
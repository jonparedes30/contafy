from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from empresa.models import Empresa

User = get_user_model()

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
            
            # Buscar empresa asociada (relación ManyToMany)
            try:
                empresas = user.empresas.all()
                if empresas.exists():
                    for empresa in empresas:
                        self.stdout.write(f"Empresa: {empresa.nombre} ({empresa.categoria})")
                else:
                    self.stdout.write("Empresa: NO TIENE EMPRESA ASOCIADA")
            except Exception as e:
                self.stdout.write(f"Error al buscar empresa: {str(e)}")
                self.stdout.write("Empresa: ERROR AL VERIFICAR")
            
            self.stdout.write("---")
        
        self.stdout.write(f"\nTotal usuarios: {users.count()}")
        
        # Mostrar todas las empresas
        self.stdout.write("\n=== TODAS LAS EMPRESAS ===")
        empresas = Empresa.objects.all()
        for empresa in empresas:
            usuarios_count = empresa.usuarios.count()
            self.stdout.write(f"ID: {empresa.id} - {empresa.nombre} - Usuarios: {usuarios_count}")
            if usuarios_count > 0:
                for usuario in empresa.usuarios.all():
                    self.stdout.write(f"  -> Usuario: {usuario.username}")
        
        self.stdout.write(f"\nTotal empresas: {empresas.count()}")
        
        # Mostrar usuarios más recientes primero
        self.stdout.write("\n=== USUARIOS RECIENTES (ULTIMOS 10) ===")
        usuarios_recientes = User.objects.all().order_by('-date_joined')[:10]
        for user in usuarios_recientes:
            self.stdout.write(f"{user.id}: {user.username} - {user.email} - {user.date_joined}")
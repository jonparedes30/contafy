from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model, authenticate
from empresa.models import Empresa

User = get_user_model()

class Command(BaseCommand):
    help = 'Debug del sistema de login'

    def handle(self, *args, **options):
        self.stdout.write("=== DEBUG LOGIN SYSTEM ===")
        
        # Verificar usuarios
        users = User.objects.all()
        self.stdout.write(f"Total usuarios: {users.count()}")
        
        for user in users:
            self.stdout.write(f"\nUsuario: {user.username}")
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"Activo: {user.is_active}")
            self.stdout.write(f"Staff: {user.is_staff}")
            self.stdout.write(f"Superuser: {user.is_superuser}")
            self.stdout.write(f"Password hash: {user.password[:50]}...")
            
            # Probar autenticación
            if user.username == 'admin':
                passwords = ['admin123', 'admin', 'password', '123456']
                for pwd in passwords:
                    auth_user = authenticate(username=user.username, password=pwd)
                    if auth_user:
                        self.stdout.write(f"✅ Password '{pwd}' FUNCIONA")
                        break
                    else:
                        self.stdout.write(f"❌ Password '{pwd}' no funciona")
        
        # Crear superusuario de emergencia
        self.stdout.write("\n=== CREANDO SUPERUSUARIO DE EMERGENCIA ===")
        
        # Eliminar admin existente si hay problemas
        try:
            admin_user = User.objects.get(username='admin')
            admin_user.delete()
            self.stdout.write("Admin anterior eliminado")
        except User.DoesNotExist:
            pass
        
        # Crear empresa admin
        empresa_admin, created = Empresa.objects.get_or_create(
            nombre='Admin CONTAFY',
            defaults={
                'ruc': '0000000000001',
                'direccion': 'Admin',
                'categoria': 'servicios'
            }
        )
        
        # Crear nuevo superusuario
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@contafy.com',
            password='contafy123',
            empresa=empresa_admin
        )
        
        self.stdout.write("✅ Nuevo superusuario creado:")
        self.stdout.write("Usuario: admin")
        self.stdout.write("Password: contafy123")
        self.stdout.write("Email: admin@contafy.com")
        
        # Verificar que funciona
        test_auth = authenticate(username='admin', password='contafy123')
        if test_auth:
            self.stdout.write("✅ Autenticación verificada - FUNCIONA")
        else:
            self.stdout.write("❌ Autenticación falló")
        
        self.stdout.write("\n=== URLS PARA PROBAR ===")
        self.stdout.write("Login: /app-beta-2024/login/")
        self.stdout.write("Admin Simple: /app-beta-2024/admin-simple/")
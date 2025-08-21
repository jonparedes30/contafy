from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from empresa.models import Empresa

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea admin simple sin eliminar el anterior'

    def handle(self, *args, **options):
        self.stdout.write("=== CREANDO ADMIN SIMPLE ===")
        
        # Crear empresa admin
        empresa_admin, created = Empresa.objects.get_or_create(
            nombre='Admin Simple CONTAFY',
            defaults={
                'ruc': '0000000000002',
                'direccion': 'Admin Simple',
                'categoria': 'servicios'
            }
        )
        
        # Eliminar admin_simple si existe
        try:
            User.objects.filter(username='admin_simple').delete()
            self.stdout.write("Admin simple anterior eliminado")
        except:
            pass
        
        # Crear nuevo superusuario
        admin = User.objects.create_superuser(
            username='admin_simple',
            email='admin_simple@contafy.com',
            password='contafy123',
            empresa=empresa_admin
        )
        
        self.stdout.write("✅ Admin simple creado:")
        self.stdout.write("Usuario: admin_simple")
        self.stdout.write("Password: contafy123")
        self.stdout.write("Email: admin_simple@contafy.com")
        
        # Verificar que funciona
        from django.contrib.auth import authenticate
        test_auth = authenticate(username='admin_simple', password='contafy123')
        if test_auth:
            self.stdout.write("✅ Autenticación verificada - FUNCIONA")
        else:
            self.stdout.write("❌ Autenticación falló")
        
        self.stdout.write("\n=== INSTRUCCIONES ===")
        self.stdout.write("1. Ir a: /app-beta-2024/login/")
        self.stdout.write("2. Usuario: admin_simple")
        self.stdout.write("3. Password: contafy123")
        self.stdout.write("4. Luego ir a: /app-beta-2024/admin-simple/")
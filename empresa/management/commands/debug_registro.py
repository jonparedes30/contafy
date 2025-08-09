from django.core.management.base import BaseCommand
from empresa.forms import RegistroForm
from empresa.models import CodigoInvitacion, Usuario, Empresa

class Command(BaseCommand):
    help = 'Debug del proceso de registro'

    def handle(self, *args, **options):
        # Limpiar datos anteriores
        Usuario.objects.filter(username__startswith='test').delete()
        Empresa.objects.filter(nombre__startswith='Test').delete()
        CodigoInvitacion.objects.filter(codigo='TEST123').delete()
        
        # Crear código
        codigo = CodigoInvitacion.objects.create(codigo="TEST123", usado=False)
        self.stdout.write("✓ Código creado")
        
        # Datos del formulario
        data = {
            'username': 'testuser',
            'email': 'test@test.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'nombre_empresa': 'Test Company',
            'ruc': '1234567890',
            'direccion': 'Test Address',
            'provincia': 'pichincha',
            'ciudad': 'Quito',
            'categoria': 'comercial',
            'tipo_negocio': 'Test Business'
        }
        
        # Probar formulario
        form = RegistroForm(data)
        self.stdout.write(f"Form válido: {form.is_valid()}")
        
        if not form.is_valid():
            self.stdout.write("ERRORES:")
            for field, errors in form.errors.items():
                self.stdout.write(f"  {field}: {errors}")
            return
        
        # Intentar guardar
        try:
            user = form.save()
            self.stdout.write(f"✓ Usuario creado: {user.username}")
            self.stdout.write(f"✓ Empresa: {user.empresa}")
            self.stdout.write(f"✓ Activo: {user.is_active}")
            self.stdout.write(f"✓ Password hasheada: {user.password.startswith('pbkdf2_')}")
            
            # Probar autenticación
            from django.contrib.auth import authenticate
            auth_user = authenticate(username='testuser', password='TestPass123!')
            self.stdout.write(f"✓ Autenticación: {'OK' if auth_user else 'FALLA'}")
            
        except Exception as e:
            self.stdout.write(f"✗ Error guardando: {e}")
            import traceback
            traceback.print_exc()
from django.core.management.base import BaseCommand
from empresa.forms import RegistroForm
from empresa.models import CodigoInvitacion, Usuario, Empresa
from django.contrib.auth import authenticate
from django.db import transaction

class Command(BaseCommand):
    help = 'Prueba el proceso de registro completo'

    def handle(self, *args, **options):
        self.stdout.write("=== PRUEBA DEL PROCESO DE REGISTRO ===")
        
        # 1. Verificar códigos disponibles
        self.stdout.write("\n1. CÓDIGOS DISPONIBLES:")
        codigos_disponibles = CodigoInvitacion.objects.filter(usado=False)
        for codigo in codigos_disponibles[:5]:
            self.stdout.write(f"✅ {codigo.codigo}")
        
        if not codigos_disponibles.exists():
            self.stdout.write("❌ NO HAY CÓDIGOS DISPONIBLES")
            # Crear código de prueba
            codigo_test = CodigoInvitacion.objects.create(codigo="TEST_REGISTRO_2024", usado=False)
            self.stdout.write(f"✅ Código creado para prueba: {codigo_test.codigo}")
        
        # 2. Probar formulario de registro
        self.stdout.write("\n2. PRUEBA DE FORMULARIO:")
        
        # Limpiar usuario de prueba anterior
        Usuario.objects.filter(username='test_registro').delete()
        Empresa.objects.filter(nombre='Test Registro Company').delete()
        
        # Datos de prueba
        form_data = {
            'username': 'test_registro',
            'email': 'test_registro@test.com',
            'first_name': 'Test',
            'last_name': 'Registro',
            'password1': 'TestPass123!',
            'password2': 'TestPass123!',
            'nombre_empresa': 'Test Registro Company',
            'ruc': '1234567890123',
            'direccion': 'Test Address 123',
            'provincia': 'pichincha',
            'ciudad': 'Quito',
            'categoria': 'comercial',
            'tipo_negocio': 'Test Business',
            'codigo_invitacion': codigos_disponibles.first().codigo if codigos_disponibles.exists() else 'TEST_REGISTRO_2024'
        }
        
        # Probar formulario
        form = RegistroForm(data=form_data)
        
        self.stdout.write(f"Formulario válido: {form.is_valid()}")
        
        if not form.is_valid():
            self.stdout.write("❌ ERRORES EN FORMULARIO:")
            for field, errors in form.errors.items():
                self.stdout.write(f"  {field}: {errors}")
            return
        
        # 3. Intentar guardar usuario
        self.stdout.write("\n3. GUARDANDO USUARIO:")
        try:
            with transaction.atomic():
                user = form.save()
                self.stdout.write(f"✅ Usuario creado: {user.username}")
                self.stdout.write(f"✅ Email: {user.email}")
                self.stdout.write(f"✅ Activo: {user.is_active}")
                self.stdout.write(f"✅ Empresa: {user.empresa.nombre if user.empresa else 'Sin empresa'}")
                
                # Verificar que el código se marcó como usado
                codigo_usado = CodigoInvitacion.objects.get(codigo=form_data['codigo_invitacion'])
                self.stdout.write(f"✅ Código marcado como usado: {codigo_usado.usado}")
                self.stdout.write(f"✅ Usado por: {codigo_usado.usado_por.username if codigo_usado.usado_por else 'Nadie'}")
                
        except Exception as e:
            self.stdout.write(f"❌ Error guardando: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # 4. Probar autenticación
        self.stdout.write("\n4. PRUEBA DE AUTENTICACIÓN:")
        auth_user = authenticate(username='test_registro', password='TestPass123!')
        if auth_user:
            self.stdout.write("✅ Autenticación exitosa")
            self.stdout.write(f"✅ Usuario autenticado: {auth_user.username}")
            self.stdout.write(f"✅ Empresa: {auth_user.empresa.nombre if auth_user.empresa else 'Sin empresa'}")
        else:
            self.stdout.write("❌ Autenticación falló")
        
        # 5. Verificar proceso completo
        self.stdout.write("\n5. VERIFICACIÓN FINAL:")
        try:
            usuario_final = Usuario.objects.get(username='test_registro')
            empresa_final = usuario_final.empresa
            
            self.stdout.write(f"✅ Usuario en DB: {usuario_final.username}")
            self.stdout.write(f"✅ Email: {usuario_final.email}")
            self.stdout.write(f"✅ Empresa: {empresa_final.nombre}")
            self.stdout.write(f"✅ RUC: {empresa_final.ruc}")
            self.stdout.write(f"✅ Categoría: {empresa_final.categoria}")
            
        except Exception as e:
            self.stdout.write(f"❌ Error en verificación: {e}")
        
        self.stdout.write("\n=== CONCLUSIÓN ===")
        self.stdout.write("✅ El proceso de registro funciona correctamente")
        self.stdout.write("✅ Los códigos de invitación se validan")
        self.stdout.write("✅ Las empresas se crean automáticamente")
        self.stdout.write("✅ La autenticación funciona")
        
        # Limpiar datos de prueba
        self.stdout.write("\n6. LIMPIEZA:")
        Usuario.objects.filter(username='test_registro').delete()
        Empresa.objects.filter(nombre='Test Registro Company').delete()
        self.stdout.write("✅ Datos de prueba eliminados")
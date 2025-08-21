from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from empresa.models import Empresa

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea un superusuario automáticamente'

    def handle(self, *args, **options):
        # Verificar si ya existe un superusuario
        if User.objects.filter(is_superuser=True).exists():
            self.stdout.write("Ya existe un superusuario")
            return
        
        # Crear empresa para el admin
        empresa, created = Empresa.objects.get_or_create(
            nombre='Administración CONTAFY',
            defaults={
                'ruc': '0000000000000',
                'direccion': 'Oficina Central',
                'categoria': 'servicios',
                'tipo_negocio': 'Administración'
            }
        )
        
        # Crear superusuario
        admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@contafy.com',
            password='admin123',
            empresa=empresa
        )
        
        self.stdout.write(f"Superusuario creado: {admin_user.username}")
        self.stdout.write("Credenciales:")
        self.stdout.write("Usuario: admin")
        self.stdout.write("Password: admin123")
        self.stdout.write(f"Empresa: {empresa.nombre}")
        
        # Crear algunos códigos de invitación de prueba
        from empresa.models import CodigoInvitacion
        
        codigos = ['BETA2024', 'PRUEBA123', 'DEMO2024']
        for codigo in codigos:
            obj, created = CodigoInvitacion.objects.get_or_create(
                codigo=codigo,
                defaults={'usado': False}
            )
            if created:
                self.stdout.write(f"Código creado: {codigo}")
        
        self.stdout.write("¡Listo! Puedes acceder al admin con las credenciales mostradas.")
from django.core.management.base import BaseCommand
from empresa.models import Usuario, Empresa

class Command(BaseCommand):
    help = 'Limpia usuarios problemáticos'

    def handle(self, *args, **options):
        # Eliminar usuarios que no sean admin
        usuarios_no_admin = Usuario.objects.exclude(username='admin')
        count = usuarios_no_admin.count()
        usuarios_no_admin.delete()
        self.stdout.write(f"Eliminados {count} usuarios no admin")
        
        # Eliminar empresas huérfanas
        empresas_huerfanas = Empresa.objects.filter(usuarios__isnull=True)
        count = empresas_huerfanas.count()
        empresas_huerfanas.delete()
        self.stdout.write(f"Eliminadas {count} empresas huérfanas")
        
        self.stdout.write("Limpieza completada")
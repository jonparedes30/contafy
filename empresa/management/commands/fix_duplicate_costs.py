from django.core.management.base import BaseCommand
from empresa.models import MovimientoContable

class Command(BaseCommand):
    help = 'Elimina asientos de costo duplicados que terminan con - CORREGIDO'
    
    def handle(self, *args, **options):
        # Eliminar movimientos duplicados de costo que terminan con "- CORREGIDO"
        duplicados = MovimientoContable.objects.filter(
            descripcion__endswith='- CORREGIDO'
        )
        
        count = duplicados.count()
        self.stdout.write(f"Eliminando {count} movimientos duplicados...")
        
        duplicados.delete()
        
        self.stdout.write(f"Eliminados {count} movimientos duplicados de costo")
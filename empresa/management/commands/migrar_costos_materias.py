from django.core.management.base import BaseCommand
from empresa.models import ConsumoMateriaPrima, MovimientoContable, CuentaContable
from empresa.views.contabilidad import registrar_movimiento_contable

class Command(BaseCommand):
    help = 'Migra consumos de materias primas existentes como costos contables'

    def handle(self, *args, **options):
        consumos = ConsumoMateriaPrima.objects.all()
        migrados = 0
        
        for consumo in consumos:
            try:
                # Registrar como costo contable
                registrar_movimiento_contable(
                    empresa=consumo.empresa,
                    cuenta_debito_nombre='Costo de Ventas',
                    cuenta_credito_nombre='Inventario de Materias Primas',
                    monto=consumo.costo_total,
                    descripcion=f"Migración: Consumo de {consumo.materia_prima.nombre} - {consumo.cantidad_consumida} unidades"
                )
                migrados += 1
                self.stdout.write(f"OK Migrado: {consumo.materia_prima.nombre} - ${consumo.costo_total}")
            except Exception as e:
                self.stdout.write(f"ERROR: {consumo.materia_prima.nombre} - {e}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Migración completada: {migrados} consumos migrados como costos contables')
        )
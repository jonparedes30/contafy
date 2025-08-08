from django.core.management.base import BaseCommand
from empresa.models import MateriaPrima, MovimientoContable, CuentaContable
from empresa.views.contabilidad import registrar_movimiento_contable

class Command(BaseCommand):
    help = 'Migra compras iniciales de materias primas existentes como activos contables'

    def handle(self, *args, **options):
        materias_primas = MateriaPrima.objects.filter(stock_actual__gt=0)
        migrados = 0
        
        for materia in materias_primas:
            try:
                # Verificar si ya existe el movimiento para evitar duplicados
                cuenta_inventario = CuentaContable.objects.filter(
                    empresa=materia.empresa,
                    nombre__iexact='Inventario de Materias Primas'
                ).first()
                
                if cuenta_inventario:
                    # Verificar si ya hay movimientos para esta materia prima
                    movimiento_existente = MovimientoContable.objects.filter(
                        empresa=materia.empresa,
                        cuenta_fk=cuenta_inventario,
                        descripcion__icontains=materia.nombre
                    ).exists()
                    
                    if movimiento_existente:
                        self.stdout.write(f"SKIP: {materia.nombre} - ya migrado")
                        continue
                
                # Registrar compra inicial como activo
                costo_total = materia.stock_actual * materia.precio_unitario
                
                registrar_movimiento_contable(
                    empresa=materia.empresa,
                    cuenta_debito_nombre='Inventario de Materias Primas',
                    cuenta_credito_nombre='Caja/Banco',
                    monto=costo_total,
                    descripcion=f"Migración: Compra inicial de {materia.nombre} - {materia.stock_actual} {materia.unidad_medida}",
                    tipo_cuenta_debito='activo',
                    tipo_cuenta_credito='activo'
                )
                
                migrados += 1
                self.stdout.write(f"OK Migrado: {materia.nombre} - ${costo_total}")
                
            except Exception as e:
                self.stdout.write(f"ERROR: {materia.nombre} - {e}")
        
        self.stdout.write(
            self.style.SUCCESS(f'Migración completada: {migrados} compras de materias primas migradas como activos')
        )
from django.core.management.base import BaseCommand
from empresa.models import MovimientoContable, CuentaContable
from django.db.models import Sum

class Command(BaseCommand):
    help = 'Verifica que la contabilidad de manufactura esté correcta'

    def handle(self, *args, **options):
        # Obtener todas las empresas de manufactura
        from empresa.models import Empresa
        empresas_manufactura = Empresa.objects.filter(categoria='manufactura')
        
        for empresa in empresas_manufactura:
            self.stdout.write(f"\n=== EMPRESA: {empresa.nombre} ===")
            
            # 1. Inventario de Materias Primas (ACTIVO)
            try:
                cuenta_inventario = CuentaContable.objects.get(
                    empresa=empresa, 
                    nombre__iexact='Inventario de Materias Primas'
                )
                debitos = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_inventario, tipo='debito'
                ).aggregate(total=Sum('monto'))['total'] or 0
                creditos = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_inventario, tipo='credito'
                ).aggregate(total=Sum('monto'))['total'] or 0
                saldo_inventario = debitos - creditos
                self.stdout.write(f"Inventario Materias Primas: ${saldo_inventario} (Débitos: ${debitos}, Créditos: ${creditos})")
            except CuentaContable.DoesNotExist:
                self.stdout.write("Inventario Materias Primas: NO EXISTE")
            
            # 2. Costo de Ventas (GASTO)
            try:
                cuenta_costo = CuentaContable.objects.get(
                    empresa=empresa, 
                    nombre__iexact='Costo de Ventas'
                )
                debitos = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_costo, tipo='debito'
                ).aggregate(total=Sum('monto'))['total'] or 0
                creditos = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_costo, tipo='credito'
                ).aggregate(total=Sum('monto'))['total'] or 0
                saldo_costo = debitos - creditos
                self.stdout.write(f"Costo de Ventas: ${saldo_costo} (Débitos: ${debitos}, Créditos: ${creditos})")
            except CuentaContable.DoesNotExist:
                self.stdout.write("Costo de Ventas: NO EXISTE")
            
            # 3. Ventas (INGRESO)
            try:
                cuenta_ventas = CuentaContable.objects.get(
                    empresa=empresa, 
                    nombre__iexact='Ventas'
                )
                debitos = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_ventas, tipo='debito'
                ).aggregate(total=Sum('monto'))['total'] or 0
                creditos = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_ventas, tipo='credito'
                ).aggregate(total=Sum('monto'))['total'] or 0
                saldo_ventas = creditos - debitos
                self.stdout.write(f"Ventas: ${saldo_ventas} (Débitos: ${debitos}, Créditos: ${creditos})")
            except CuentaContable.DoesNotExist:
                self.stdout.write("Ventas: NO EXISTE")
            
            # 4. Caja/Banco (ACTIVO)
            try:
                cuenta_caja = CuentaContable.objects.get(
                    empresa=empresa, 
                    nombre__iexact='Caja/Banco'
                )
                debitos = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_caja, tipo='debito'
                ).aggregate(total=Sum('monto'))['total'] or 0
                creditos = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta_caja, tipo='credito'
                ).aggregate(total=Sum('monto'))['total'] or 0
                saldo_caja = debitos - creditos
                self.stdout.write(f"Caja/Banco: ${saldo_caja} (Débitos: ${debitos}, Créditos: ${creditos})")
            except CuentaContable.DoesNotExist:
                self.stdout.write("Caja/Banco: NO EXISTE")
        
        self.stdout.write(self.style.SUCCESS('\nVerificación completada'))
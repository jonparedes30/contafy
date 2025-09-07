from django.core.management.base import BaseCommand
from django.db.models import Sum
from empresa.models import Empresa, Venta, Gasto, Compra, MovimientoContable, CuentaContable
from datetime import datetime

class Command(BaseCommand):
    help = 'Verifica integridad del flujo de caja y detecta duplicidad'
    
    def handle(self, *args, **options):
        self.stdout.write("=== VERIFICACIÓN DE INTEGRIDAD FLUJO DE CAJA ===\n")
        
        empresas = Empresa.objects.all()
        año_actual = datetime.now().year
        
        for empresa in empresas:
            self.stdout.write(f"--- Empresa: {empresa.nombre} ---")
            
            # Comparar método directo vs movimientos contables
            self.comparar_metodos_calculo(empresa, año_actual)
            
            # Verificar duplicados en movimientos contables
            self.verificar_duplicados_movimientos(empresa)
            
            self.stdout.write("")
    
    def comparar_metodos_calculo(self, empresa, año):
        """Compara cálculo directo vs movimientos contables"""
        
        # MÉTODO DIRECTO (sin duplicados)
        ventas_directas = Venta.objects.filter(
            empresa=empresa,
            fecha__year=año,
            tipo_pago='contado'
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        gastos_directos = Gasto.objects.filter(
            empresa=empresa,
            fecha__year=año,
            tipo_pago='contado'
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        compras_directas = Compra.objects.filter(
            empresa=empresa,
            fecha__year=año,
            tipo_pago='contado'
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        flujo_directo = ventas_directas - gastos_directos - compras_directas
        
        # MÉTODO CONTABLE (puede tener duplicados)
        try:
            cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
            ventas_contables = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_ventas,
                tipo='credito',
                fecha__year=año
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            ventas_contables = 0
        
        try:
            cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
            gastos_contables = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_gastos,
                tipo='debito',
                fecha__year=año
            ).aggregate(total=Sum('monto'))['total'] or 0
        except CuentaContable.DoesNotExist:
            gastos_contables = 0
        
        flujo_contable = ventas_contables - gastos_contables
        
        # Comparar resultados
        diferencia = abs(flujo_directo - flujo_contable)
        
        self.stdout.write(f"  Método Directo:")
        self.stdout.write(f"    Ventas contado: ${ventas_directas}")
        self.stdout.write(f"    Gastos contado: ${gastos_directos}")
        self.stdout.write(f"    Compras contado: ${compras_directas}")
        self.stdout.write(f"    Flujo neto: ${flujo_directo}")
        
        self.stdout.write(f"  Método Contable:")
        self.stdout.write(f"    Ventas (movimientos): ${ventas_contables}")
        self.stdout.write(f"    Gastos (movimientos): ${gastos_contables}")
        self.stdout.write(f"    Flujo neto: ${flujo_contable}")
        
        if diferencia > 1.0:  # Diferencia mayor a $1
            self.stdout.write(f"  ⚠️  DIFERENCIA: ${diferencia} - Posible duplicidad")
        else:
            self.stdout.write(f"  ✅ Consistente (diferencia: ${diferencia})")
    
    def verificar_duplicados_movimientos(self, empresa):
        """Verifica duplicados específicos en movimientos contables"""
        
        # Buscar movimientos con descripción de ajuste automático
        ajustes = MovimientoContable.objects.filter(
            empresa=empresa,
            descripcion__icontains='AJUSTE AUTOMÁTICO'
        ).count()
        
        if ajustes > 0:
            self.stdout.write(f"  ⚠️  {ajustes} movimientos de ajuste automático encontrados")
            
            # Contar por tipo de ajuste
            ajustes_venta = MovimientoContable.objects.filter(
                empresa=empresa,
                descripcion__icontains='Venta',
                descripcion__icontains='AJUSTE AUTOMÁTICO'
            ).count()
            
            ajustes_gasto = MovimientoContable.objects.filter(
                empresa=empresa,
                descripcion__icontains='Gasto',
                descripcion__icontains='AJUSTE AUTOMÁTICO'
            ).count()
            
            if ajustes_venta > 0:
                self.stdout.write(f"     - Ajustes de ventas: {ajustes_venta}")
            if ajustes_gasto > 0:
                self.stdout.write(f"     - Ajustes de gastos: {ajustes_gasto}")
        else:
            self.stdout.write(f"  ✅ Sin ajustes automáticos")
        
        # Verificar movimientos exactamente duplicados
        from collections import defaultdict
        movimientos = MovimientoContable.objects.filter(empresa=empresa)
        
        grupos = defaultdict(list)
        for mov in movimientos:
            # Agrupar por monto, tipo y descripción base (sin ajustes)
            desc_base = mov.descripcion.split(' - AJUSTE')[0]
            key = (mov.monto, mov.tipo, desc_base)
            grupos[key].append(mov)
        
        duplicados_exactos = sum(1 for grupo in grupos.values() if len(grupo) > 1)
        
        if duplicados_exactos > 0:
            self.stdout.write(f"  ⚠️  {duplicados_exactos} grupos de movimientos duplicados")
        else:
            self.stdout.write(f"  ✅ Sin duplicados exactos")
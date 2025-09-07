from django.core.management.base import BaseCommand
from django.db.models import Count, Sum
from empresa.models import *
from collections import defaultdict
import json

class Command(BaseCommand):
    help = 'Verifica integridad de datos, duplicados y consistencia entre modelos'
    
    def handle(self, *args, **options):
        self.stdout.write("=== VERIFICACIÓN INTEGRAL DE DATOS ===\n")
        
        # 1. Verificar duplicados
        self.verificar_duplicados()
        
        # 2. Verificar consistencia contable
        self.verificar_consistencia_contable()
        
        # 3. Verificar relaciones entre modelos
        self.verificar_relaciones()
        
        # 4. Verificar datos huérfanos
        self.verificar_huerfanos()
        
        # 5. Verificar integridad de stock
        self.verificar_stock()
        
        self.stdout.write("\n=== VERIFICACIÓN COMPLETADA ===")
    
    def verificar_duplicados(self):
        self.stdout.write("1. VERIFICANDO DUPLICADOS:")
        
        # Productos duplicados por empresa
        productos_dup = Producto.objects.values('empresa', 'codigo').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if productos_dup:
            self.stdout.write(f"  ❌ {productos_dup.count()} códigos de productos duplicados")
            for dup in productos_dup[:5]:
                self.stdout.write(f"     - Empresa {dup['empresa']}: código '{dup['codigo']}' ({dup['count']} veces)")
        else:
            self.stdout.write("  ✅ No hay productos duplicados")
        
        # Clientes duplicados por empresa
        clientes_dup = Cliente.objects.values('empresa', 'numero_documento').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if clientes_dup:
            self.stdout.write(f"  ❌ {clientes_dup.count()} documentos de clientes duplicados")
        else:
            self.stdout.write("  ✅ No hay clientes duplicados")
        
        # Movimientos contables duplicados (mismo monto, fecha, descripción)
        movimientos_dup = MovimientoContable.objects.values(
            'empresa', 'monto', 'descripcion', 'fecha__date'
        ).annotate(count=Count('id')).filter(count__gt=5)  # Más de 5 iguales es sospechoso
        
        if movimientos_dup:
            self.stdout.write(f"  ⚠️  {movimientos_dup.count()} grupos de movimientos posiblemente duplicados")
            for dup in movimientos_dup[:3]:
                self.stdout.write(f"     - ${dup['monto']} '{dup['descripcion'][:50]}...' ({dup['count']} veces)")
        else:
            self.stdout.write("  ✅ No hay movimientos contables sospechosos")
    
    def verificar_consistencia_contable(self):
        self.stdout.write("\n2. VERIFICANDO CONSISTENCIA CONTABLE:")
        
        empresas = Empresa.objects.all()
        for empresa in empresas:
            # Verificar que ventas tengan movimientos contables
            ventas_sin_movimientos = []
            ventas = Venta.objects.filter(empresa=empresa)[:10]  # Muestra de 10
            
            for venta in ventas:
                movimientos = MovimientoContable.objects.filter(
                    empresa=empresa,
                    descripcion__icontains=venta.producto.nombre
                )
                if not movimientos.exists():
                    ventas_sin_movimientos.append(venta.id)
            
            if ventas_sin_movimientos:
                self.stdout.write(f"  ❌ {empresa.nombre}: {len(ventas_sin_movimientos)} ventas sin movimientos contables")
            else:
                self.stdout.write(f"  ✅ {empresa.nombre}: Ventas tienen movimientos contables")
            
            # Verificar sumas de cuentas contables
            cuentas = CuentaContable.objects.filter(empresa=empresa)
            for cuenta in cuentas[:5]:  # Muestra de 5 cuentas
                valor_calculado = cuenta.valor
                movimientos_suma = MovimientoContable.objects.filter(
                    empresa=empresa, cuenta_fk=cuenta
                )
                
                if movimientos_suma.exists():
                    debitos = sum(m.monto for m in movimientos_suma if m.tipo == 'debito')
                    creditos = sum(m.monto for m in movimientos_suma if m.tipo == 'credito')
                    
                    if cuenta.tipo in ['activo', 'gasto']:
                        esperado = debitos - creditos
                    else:
                        esperado = creditos - debitos
                    
                    if abs(valor_calculado - esperado) > 0.01:
                        self.stdout.write(f"  ❌ {cuenta.nombre}: Valor=${valor_calculado}, Esperado=${esperado}")
    
    def verificar_relaciones(self):
        self.stdout.write("\n3. VERIFICANDO RELACIONES ENTRE MODELOS:")
        
        # Verificar que todas las ventas tengan productos válidos
        ventas_producto_invalido = Venta.objects.filter(producto__isnull=True).count()
        if ventas_producto_invalido:
            self.stdout.write(f"  ❌ {ventas_producto_invalido} ventas sin producto válido")
        else:
            self.stdout.write("  ✅ Todas las ventas tienen productos válidos")
        
        # Verificar que todos los movimientos tengan cuenta_fk
        movimientos_sin_cuenta = MovimientoContable.objects.filter(cuenta_fk__isnull=True).count()
        if movimientos_sin_cuenta:
            self.stdout.write(f"  ❌ {movimientos_sin_cuenta} movimientos sin cuenta_fk")
        else:
            self.stdout.write("  ✅ Todos los movimientos tienen cuenta_fk")
        
        # Verificar cuentas por cobrar vs ventas a crédito
        empresas = Empresa.objects.all()[:3]  # Muestra de 3 empresas
        for empresa in empresas:
            ventas_credito = Venta.objects.filter(empresa=empresa, tipo_pago='credito').count()
            cuentas_cobrar = CuentaPorCobrar.objects.filter(empresa=empresa).count()
            
            if ventas_credito > 0 and cuentas_cobrar == 0:
                self.stdout.write(f"  ⚠️  {empresa.nombre}: {ventas_credito} ventas a crédito pero 0 cuentas por cobrar")
    
    def verificar_huerfanos(self):
        self.stdout.write("\n4. VERIFICANDO DATOS HUÉRFANOS:")
        
        # Movimientos contables sin empresa
        movimientos_huerfanos = MovimientoContable.objects.filter(empresa__isnull=True).count()
        if movimientos_huerfanos:
            self.stdout.write(f"  ❌ {movimientos_huerfanos} movimientos sin empresa")
        else:
            self.stdout.write("  ✅ Todos los movimientos tienen empresa")
        
        # Productos sin empresa
        productos_huerfanos = Producto.objects.filter(empresa__isnull=True).count()
        if productos_huerfanos:
            self.stdout.write(f"  ❌ {productos_huerfanos} productos sin empresa")
        else:
            self.stdout.write("  ✅ Todos los productos tienen empresa")
        
        # Cuentas contables sin movimientos (posibles huérfanas)
        cuentas_sin_movimientos = CuentaContable.objects.filter(movimientos__isnull=True).count()
        if cuentas_sin_movimientos:
            self.stdout.write(f"  ⚠️  {cuentas_sin_movimientos} cuentas contables sin movimientos")
    
    def verificar_stock(self):
        self.stdout.write("\n5. VERIFICANDO INTEGRIDAD DE STOCK:")
        
        empresas = Empresa.objects.all()[:3]  # Muestra de 3 empresas
        for empresa in empresas:
            productos_stock_negativo = Producto.objects.filter(
                empresa=empresa, stock__lt=0
            ).count()
            
            if productos_stock_negativo:
                self.stdout.write(f"  ❌ {empresa.nombre}: {productos_stock_negativo} productos con stock negativo")
            else:
                self.stdout.write(f"  ✅ {empresa.nombre}: Stock de productos correcto")
            
            # Verificar consistencia entre ventas y stock
            productos_problema = []
            productos = Producto.objects.filter(empresa=empresa)[:5]  # Muestra de 5
            
            for producto in productos:
                ventas_cantidad = Venta.objects.filter(
                    empresa=empresa, producto=producto
                ).aggregate(total=Sum('cantidad'))['total'] or 0
                
                compras_cantidad = Compra.objects.filter(
                    empresa=empresa, producto=producto
                ).aggregate(total=Sum('cantidad'))['total'] or 0
                
                stock_teorico = compras_cantidad - ventas_cantidad
                
                if abs(producto.stock - stock_teorico) > 5:  # Diferencia mayor a 5 unidades
                    productos_problema.append({
                        'producto': producto.nombre,
                        'stock_actual': producto.stock,
                        'stock_teorico': stock_teorico,
                        'diferencia': abs(producto.stock - stock_teorico)
                    })
            
            if productos_problema:
                self.stdout.write(f"  ⚠️  {empresa.nombre}: {len(productos_problema)} productos con inconsistencias de stock")
                for p in productos_problema[:2]:
                    self.stdout.write(f"     - {p['producto']}: Real={p['stock_actual']}, Teórico={p['stock_teorico']}")
    
    def verificar_templates_consistency(self):
        """Verifica que los datos se pasen correctamente a templates"""
        self.stdout.write("\n6. VERIFICANDO CONSISTENCIA CON TEMPLATES:")
        
        # Esta verificación requeriría análisis de templates
        # Por ahora, verificamos que los campos necesarios existan en los modelos
        
        # Campos requeridos para estado de resultados
        campos_requeridos = {
            'Venta': ['monto', 'monto_neto', 'iva', 'fecha'],
            'Gasto': ['monto', 'fecha', 'descripcion'],
            'CuentaContable': ['nombre', 'tipo', 'valor'],
        }
        
        for modelo_nombre, campos in campos_requeridos.items():
            modelo = globals().get(modelo_nombre)
            if modelo:
                for campo in campos:
                    if not hasattr(modelo, campo):
                        self.stdout.write(f"  ❌ {modelo_nombre} no tiene campo '{campo}'")
                    else:
                        self.stdout.write(f"  ✅ {modelo_nombre}.{campo} existe")
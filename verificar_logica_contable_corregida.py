#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import *
from django.db.models import Sum

def verificar_logica_contable():
    print("=== VERIFICACIÓN LÓGICA CONTABLE CORREGIDA ===")
    
    for empresa in Empresa.objects.all():
        print(f"\n--- {empresa.nombre} ({empresa.categoria}) ---")
        
        # Verificar partida doble
        movimientos = MovimientoContable.objects.filter(empresa=empresa)
        total_debitos = movimientos.filter(tipo='debito').aggregate(total=Sum('monto'))['total'] or 0
        total_creditos = movimientos.filter(tipo='credito').aggregate(total=Sum('monto'))['total'] or 0
        
        print(f"Débitos: ${total_debitos:,.2f}")
        print(f"Créditos: ${total_creditos:,.2f}")
        print(f"Diferencia: ${abs(total_debitos - total_creditos):,.2f}")
        
        if abs(total_debitos - total_creditos) < 0.01:
            print("[OK] PARTIDA DOBLE BALANCEADA")
        else:
            print("[ERROR] PARTIDA DOBLE DESBALANCEADA")
        
        # Verificar cuentas existentes
        cuentas = CuentaContable.objects.filter(empresa=empresa)
        print(f"\nCuentas contables: {cuentas.count()}")
        
        cuentas_requeridas = [
            'Caja/Banco', 'Ventas', 'Costo de Ventas', 'Inventario',
            'Cuentas por Cobrar', 'Cuentas por Pagar', 'Capital', 'Gastos'
        ]
        
        if empresa.categoria == 'manufactura':
            cuentas_requeridas.extend([
                'Inventario - Materia Prima', 'Producción en Proceso',
                'Inventario - Producto Terminado'
            ])
        
        for cuenta_nombre in cuentas_requeridas:
            existe = cuentas.filter(nombre=cuenta_nombre).exists()
            status = "[OK]" if existe else "[FALTA]"
            print(f"  {status} {cuenta_nombre}")
        
        # Verificar transacciones por módulo
        ventas_count = Venta.objects.filter(empresa=empresa).count()
        compras_count = Compra.objects.filter(empresa=empresa).count()
        gastos_count = Gasto.objects.filter(empresa=empresa).count()
        capital_count = Capital.objects.filter(empresa=empresa).count()
        
        print(f"\nTransacciones registradas:")
        print(f"  Ventas: {ventas_count}")
        print(f"  Compras: {compras_count}")
        print(f"  Gastos: {gastos_count}")
        print(f"  Capital: {capital_count}")
        
        if empresa.categoria == 'manufactura':
            materias_count = MateriaPrima.objects.filter(empresa=empresa).count()
            productos_manuf_count = ProductoManufacturado.objects.filter(empresa=empresa).count()
            ordenes_count = OrdenProduccion.objects.filter(empresa=empresa).count()
            consumos_count = ConsumoMateriaPrima.objects.filter(empresa=empresa).count()
            
            print(f"  Materias Primas: {materias_count}")
            print(f"  Productos Manufacturados: {productos_manuf_count}")
            print(f"  Órdenes de Producción: {ordenes_count}")
            print(f"  Consumos de MP: {consumos_count}")

if __name__ == "__main__":
    verificar_logica_contable()
#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import Empresa, Producto, Venta
from django.db.models import Sum
from datetime import datetime, timedelta

def verificar_benchmarks():
    print("=== VERIFICACION DE BENCHMARKS Y ROTACION ===")
    
    empresas = Empresa.objects.all()
    
    for empresa in empresas:
        print(f"\n--- {empresa.nombre} ({empresa.categoria}) ---")
        
        # Calcular datos reales
        hoy = datetime.now().date()
        hace_30_dias = hoy - timedelta(days=30)
        
        # Ventas del período
        ventas_periodo = Venta.objects.filter(
            empresa=empresa,
            fecha__date__gte=hace_30_dias
        ).aggregate(
            total_monto=Sum('monto'),
            total_cantidad=Sum('cantidad')
        )
        
        ventas_monto = float(ventas_periodo['total_monto'] or 0)
        ventas_cantidad = float(ventas_periodo['total_cantidad'] or 0)
        
        # Stock actual
        stock_total = Producto.objects.filter(empresa=empresa).aggregate(
            total=Sum('stock')
        )['total'] or 1
        
        # Calcular rotación anualizada
        dias_periodo = 30
        factor_anual = 365 / dias_periodo
        rotacion_real = (ventas_cantidad * factor_anual / stock_total) if stock_total > 0 else 0
        
        # Benchmarks por sector
        if empresa.categoria == 'comercial':
            margen_sector = 15
            mejor_sector = 25
            rotacion_sector = 6
        elif empresa.categoria == 'manufactura':
            margen_sector = 25
            mejor_sector = 40
            rotacion_sector = 12
        else:  # servicios
            margen_sector = 20
            mejor_sector = 35
            rotacion_sector = 24
        
        # Calcular margen real (simplificado)
        costo_estimado = ventas_monto * 0.6
        margen_real = ((ventas_monto - costo_estimado) / ventas_monto * 100) if ventas_monto > 0 else 0
        
        print(f"  VENTAS:")
        print(f"    Monto: ${ventas_monto:,.2f}")
        print(f"    Cantidad: {ventas_cantidad:,.0f} unidades")
        
        print(f"  MARGEN:")
        print(f"    Real: {margen_real:.1f}%")
        print(f"    Promedio sector: {margen_sector}%")
        print(f"    Mejor sector: {mejor_sector}%")
        
        print(f"  ROTACION:")
        print(f"    Stock total: {stock_total:,.0f} unidades")
        print(f"    Rotación real: {rotacion_real:.1f} veces/año")
        print(f"    Benchmark sector: {rotacion_sector} veces/año")
        
        # Evaluación
        if margen_real > mejor_sector:
            eval_margen = "EXCELENTE"
        elif margen_real > margen_sector:
            eval_margen = "BUENO"
        elif margen_real > 0:
            eval_margen = "REGULAR"
        else:
            eval_margen = "CRÍTICO"
        
        if rotacion_real > rotacion_sector:
            eval_rotacion = "BUENA"
        elif rotacion_real > rotacion_sector * 0.7:
            eval_rotacion = "REGULAR"
        else:
            eval_rotacion = "BAJA"
        
        print(f"  EVALUACION:")
        print(f"    Margen: {eval_margen}")
        print(f"    Rotación: {eval_rotacion}")

if __name__ == "__main__":
    verificar_benchmarks()
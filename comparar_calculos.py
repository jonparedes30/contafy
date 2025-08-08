#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.models import Empresa, Venta, Gasto, CuentaContable, MovimientoContable
from django.db.models import Sum
from datetime import datetime, timedelta

def comparar_calculos():
    print("=== COMPARACION DE CALCULOS ===")
    
    try:
        empresa = Empresa.objects.get(nombre='ARCA')
        print(f"Empresa: {empresa.nombre}")
        print()
        
        # 1. CALCULOS DEL AGENTE IA
        print("1. CALCULOS DEL AGENTE IA:")
        agente = ContafyAIAgent()
        datos_ia = agente.obtener_datos_empresa(empresa)
        
        print(f"- Ventas mes (IA): ${datos_ia['ventas_mes']:,.2f}")
        print(f"- Gastos mes (IA): ${datos_ia['gastos_mes']:,.2f}")
        print(f"- Costo ventas (IA): ${datos_ia['costo_ventas_mes']:,.2f}")
        print(f"- Utilidad mes (IA): ${datos_ia['utilidad_mes']:,.2f}")
        print(f"- Margen (IA): {datos_ia['margen_mes']:.1f}%")
        print()
        
        # 2. CALCULOS DIRECTOS DE MODELOS
        print("2. CALCULOS DIRECTOS DE MODELOS:")
        hoy = datetime.now().date()
        hace_30_dias = hoy - timedelta(days=30)
        
        # Ventas directas del modelo Venta
        ventas_directas = Venta.objects.filter(
            empresa=empresa,
            fecha__date__gte=hace_30_dias
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        # Gastos directos del modelo Gasto
        gastos_directos = Gasto.objects.filter(
            empresa=empresa,
            fecha__date__gte=hace_30_dias
        ).aggregate(total=Sum('monto'))['total'] or 0
        
        print(f"- Ventas directas: ${ventas_directas:,.2f}")
        print(f"- Gastos directos: ${gastos_directos:,.2f}")
        print(f"- Utilidad directa: ${ventas_directas - gastos_directos:,.2f}")
        print()
        
        # 3. CALCULOS DE CUENTAS CONTABLES
        print("3. CALCULOS DE CUENTAS CONTABLES:")
        
        # Ventas desde MovimientoContable
        try:
            cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
            ventas_contables = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_ventas,
                tipo='credito',
                fecha__date__gte=hace_30_dias
            ).aggregate(total=Sum('monto'))['total'] or 0
            print(f"- Ventas contables: ${ventas_contables:,.2f}")
        except CuentaContable.DoesNotExist:
            ventas_contables = 0
            print("- Cuenta Ventas no existe")
        
        # Gastos desde MovimientoContable
        try:
            cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
            gastos_contables = MovimientoContable.objects.filter(
                empresa=empresa,
                cuenta_fk=cuenta_gastos,
                tipo='debito',
                fecha__date__gte=hace_30_dias
            ).aggregate(total=Sum('monto'))['total'] or 0
            print(f"- Gastos contables: ${gastos_contables:,.2f}")
        except CuentaContable.DoesNotExist:
            gastos_contables = 0
            print("- Cuenta Gastos no existe")
        
        print()
        
        # 4. COMPARACION Y DIFERENCIAS
        print("4. COMPARACION Y DIFERENCIAS:")
        
        diff_ventas_ia_directas = abs(datos_ia['ventas_mes'] - float(ventas_directas))
        diff_ventas_ia_contables = abs(datos_ia['ventas_mes'] - float(ventas_contables))
        diff_gastos_ia_directos = abs(datos_ia['gastos_mes'] - float(gastos_directos))
        diff_gastos_ia_contables = abs(datos_ia['gastos_mes'] - float(gastos_contables))
        
        print(f"- Diferencia ventas (IA vs Directas): ${diff_ventas_ia_directas:,.2f}")
        print(f"- Diferencia ventas (IA vs Contables): ${diff_ventas_ia_contables:,.2f}")
        print(f"- Diferencia gastos (IA vs Directos): ${diff_gastos_ia_directos:,.2f}")
        print(f"- Diferencia gastos (IA vs Contables): ${diff_gastos_ia_contables:,.2f}")
        print()
        
        # 5. DIAGNOSTICO
        print("5. DIAGNOSTICO:")
        
        if diff_ventas_ia_directas > 0.01:
            print("❌ PROBLEMA: Ventas IA ≠ Ventas directas")
            print(f"   IA usa: MovimientoContable con cuenta 'Ventas'")
            print(f"   Reportes usan: Modelo Venta directamente")
        else:
            print("✅ OK: Ventas IA = Ventas directas")
        
        if diff_gastos_ia_directos > 0.01:
            print("❌ PROBLEMA: Gastos IA ≠ Gastos directos")
            print(f"   IA usa: MovimientoContable con cuenta 'Gastos'")
            print(f"   Reportes usan: Modelo Gasto directamente")
        else:
            print("✅ OK: Gastos IA = Gastos directos")
        
        print()
        
        # 6. RECOMENDACION
        print("6. RECOMENDACION:")
        if diff_ventas_ia_directas > 0.01 or diff_gastos_ia_directos > 0.01:
            print("🔧 SOLUCION: Unificar fuente de datos")
            print("   Opción 1: IA use modelos directos (Venta, Gasto)")
            print("   Opción 2: Reportes usen MovimientoContable")
            print("   Opción 3: Sincronizar ambos sistemas")
        else:
            print("✅ Los cálculos están sincronizados correctamente")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    comparar_calculos()
#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.models import Empresa, Venta, Gasto, CuentaContable, MovimientoContable
from empresa.services.filtros_service import FiltrosFechaService
from django.db.models import Sum
from datetime import datetime, timedelta

def verificar_sincronizacion():
    print("=== VERIFICACION FINAL DE SINCRONIZACION ===")
    
    empresas = Empresa.objects.all()
    
    for empresa in empresas:
        print(f"\n--- {empresa.nombre} ({empresa.categoria}) ---")
        
        try:
            # 1. CALCULOS DEL AGENTE IA
            agente = ContafyAIAgent()
            datos_ia = agente.obtener_datos_empresa(empresa)
            
            # 2. CALCULOS DE ESTADO DE RESULTADOS (simulando la vista)
            hoy = datetime.now().date()
            hace_30_dias = hoy - timedelta(days=30)
            
            ventas_reporte = FiltrosFechaService.obtener_movimientos_contables_por_periodo(
                empresa, 'Ventas', 'credito', hace_30_dias, hoy
            )
            costos_reporte = FiltrosFechaService.obtener_movimientos_contables_por_periodo(
                empresa, 'Costo de Ventas', 'debito', hace_30_dias, hoy
            )
            gastos_reporte = FiltrosFechaService.obtener_movimientos_contables_por_periodo(
                empresa, 'Gastos', 'debito', hace_30_dias, hoy
            )
            
            utilidad_bruta_reporte = ventas_reporte - costos_reporte
            utilidad_neta_reporte = utilidad_bruta_reporte - gastos_reporte
            
            # 3. COMPARACION
            print(f"Ventas - IA: ${datos_ia['ventas_mes']:,.2f} | Reporte: ${ventas_reporte:,.2f}")
            print(f"Costos - IA: ${datos_ia['costo_ventas_mes']:,.2f} | Reporte: ${costos_reporte:,.2f}")
            print(f"Gastos - IA: ${datos_ia['gastos_mes']:,.2f} | Reporte: ${gastos_reporte:,.2f}")
            print(f"Utilidad - IA: ${datos_ia['utilidad_mes']:,.2f} | Reporte: ${utilidad_neta_reporte:,.2f}")
            
            # 4. VERIFICAR DIFERENCIAS
            diff_ventas = abs(datos_ia['ventas_mes'] - float(ventas_reporte))
            diff_costos = abs(datos_ia['costo_ventas_mes'] - float(costos_reporte))
            diff_gastos = abs(datos_ia['gastos_mes'] - float(gastos_reporte))
            diff_utilidad = abs(datos_ia['utilidad_mes'] - float(utilidad_neta_reporte))
            
            if diff_ventas < 0.01 and diff_costos < 0.01 and diff_gastos < 0.01 and diff_utilidad < 0.01:
                print("✅ SINCRONIZADO CORRECTAMENTE")
            else:
                print("❌ DIFERENCIAS ENCONTRADAS:")
                if diff_ventas > 0.01:
                    print(f"  - Ventas: ${diff_ventas:,.2f}")
                if diff_costos > 0.01:
                    print(f"  - Costos: ${diff_costos:,.2f}")
                if diff_gastos > 0.01:
                    print(f"  - Gastos: ${diff_gastos:,.2f}")
                if diff_utilidad > 0.01:
                    print(f"  - Utilidad: ${diff_utilidad:,.2f}")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
    
    print("\n=== VERIFICACION COMPLETADA ===")

if __name__ == "__main__":
    verificar_sincronizacion()
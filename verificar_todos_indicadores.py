#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.services.filtros_service import FiltrosFechaService
from empresa.models import Empresa, CuentaContable, MovimientoContable
from django.db.models import Sum
from datetime import datetime, timedelta

def verificar_todos_indicadores():
    print("=== VERIFICACION COMPLETA DE TODOS LOS INDICADORES ===")
    
    empresa = Empresa.objects.get(nombre='ARCA')
    print(f"Empresa: {empresa.nombre} ({empresa.categoria})")
    
    hoy = datetime.now().date()
    hace_30_dias = hoy - timedelta(days=30)
    
    # 1. AGENTE IA
    agente = ContafyAIAgent()
    datos_ia = agente.obtener_datos_empresa(empresa)
    
    # 2. ESTADO DE RESULTADOS
    ventas_er = FiltrosFechaService.obtener_movimientos_contables_por_periodo(
        empresa, 'Ventas', 'credito', hace_30_dias, hoy
    )
    costos_er = FiltrosFechaService.obtener_movimientos_contables_por_periodo(
        empresa, 'Costo de Ventas', 'debito', hace_30_dias, hoy
    )
    gastos_er = FiltrosFechaService.obtener_movimientos_contables_por_periodo(
        empresa, 'Gastos', 'debito', hace_30_dias, hoy
    )
    utilidad_er = ventas_er - costos_er - gastos_er
    
    # 3. BALANCE GENERAL (saldos actuales)
    try:
        total_activos = sum(c.valor for c in CuentaContable.objects.filter(empresa=empresa, tipo='activo'))
        total_pasivos = sum(c.valor for c in CuentaContable.objects.filter(empresa=empresa, tipo='pasivo'))
        total_capital = sum(c.valor for c in CuentaContable.objects.filter(empresa=empresa, tipo='capital'))
    except:
        total_activos = total_pasivos = total_capital = 0
    
    # 4. FLUJO DE CAJA (simulando cálculo)
    try:
        cuenta_ventas = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Ventas')
        entradas_fc = MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_ventas,
            tipo='credito',
            fecha__date__gte=hace_30_dias
        ).aggregate(total=Sum('monto'))['total'] or 0
    except:
        entradas_fc = 0
    
    try:
        cuenta_gastos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Gastos')
        salidas_gastos_fc = MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_gastos,
            tipo='debito',
            fecha__date__gte=hace_30_dias
        ).aggregate(total=Sum('monto'))['total'] or 0
    except:
        salidas_gastos_fc = 0
    
    try:
        cuenta_costos = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Costo de Ventas')
        salidas_costos_fc = MovimientoContable.objects.filter(
            empresa=empresa,
            cuenta_fk=cuenta_costos,
            tipo='debito',
            fecha__date__gte=hace_30_dias
        ).aggregate(total=Sum('monto'))['total'] or 0
    except:
        salidas_costos_fc = 0
    
    flujo_neto = entradas_fc - salidas_gastos_fc - salidas_costos_fc
    
    # MOSTRAR COMPARACION
    print("\n--- COMPARACION DE INDICADORES ---")
    print(f"VENTAS:")
    print(f"  IA: ${datos_ia['ventas_mes']:,.2f}")
    print(f"  Estado Resultados: ${ventas_er:,.2f}")
    print(f"  Flujo Caja: ${entradas_fc:,.2f}")
    
    print(f"\nCOSTOS:")
    print(f"  IA: ${datos_ia['costo_ventas_mes']:,.2f}")
    print(f"  Estado Resultados: ${costos_er:,.2f}")
    print(f"  Flujo Caja: ${salidas_costos_fc:,.2f}")
    
    print(f"\nGASTOS:")
    print(f"  IA: ${datos_ia['gastos_mes']:,.2f}")
    print(f"  Estado Resultados: ${gastos_er:,.2f}")
    print(f"  Flujo Caja: ${salidas_gastos_fc:,.2f}")
    
    print(f"\nUTILIDAD/FLUJO NETO:")
    print(f"  IA: ${datos_ia['utilidad_mes']:,.2f}")
    print(f"  Estado Resultados: ${utilidad_er:,.2f}")
    print(f"  Flujo Caja: ${flujo_neto:,.2f}")
    
    print(f"\nBALANCE GENERAL:")
    print(f"  Activos: ${total_activos:,.2f}")
    print(f"  Pasivos: ${total_pasivos:,.2f}")
    print(f"  Capital: ${total_capital:,.2f}")
    print(f"  Patrimonio: ${total_activos - total_pasivos:,.2f}")
    
    # VERIFICAR DIFERENCIAS
    print("\n--- VERIFICACION DE SINCRONIZACION ---")
    
    diff_ventas = abs(datos_ia['ventas_mes'] - float(ventas_er))
    diff_costos = abs(datos_ia['costo_ventas_mes'] - float(costos_er))
    diff_gastos = abs(datos_ia['gastos_mes'] - float(gastos_er))
    diff_utilidad = abs(datos_ia['utilidad_mes'] - float(utilidad_er))
    
    if diff_ventas < 0.01 and diff_costos < 0.01 and diff_gastos < 0.01 and diff_utilidad < 0.01:
        print("[OK] TODOS LOS INDICADORES SINCRONIZADOS")
    else:
        print("[ERROR] DIFERENCIAS ENCONTRADAS:")
        if diff_ventas > 0.01:
            print(f"  - Ventas: ${diff_ventas:,.2f}")
        if diff_costos > 0.01:
            print(f"  - Costos: ${diff_costos:,.2f}")
        if diff_gastos > 0.01:
            print(f"  - Gastos: ${diff_gastos:,.2f}")
        if diff_utilidad > 0.01:
            print(f"  - Utilidad: ${diff_utilidad:,.2f}")
    
    print("\n=== VERIFICACION COMPLETADA ===")

if __name__ == "__main__":
    verificar_todos_indicadores()
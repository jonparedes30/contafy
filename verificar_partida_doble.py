#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import Empresa, MovimientoContable
from django.db.models import Sum
from collections import defaultdict

def verificar_partida_doble():
    print("=== VERIFICACION DE PARTIDA DOBLE ===")
    
    empresas = Empresa.objects.all()
    
    for empresa in empresas:
        print(f"\n--- {empresa.nombre} ({empresa.categoria}) ---")
        
        # Obtener todos los movimientos
        movimientos = MovimientoContable.objects.filter(empresa=empresa)
        
        if not movimientos.exists():
            print("  Sin movimientos contables")
            continue
        
        # Agrupar por descripción (transacción)
        transacciones = defaultdict(lambda: {'debitos': 0, 'creditos': 0, 'count': 0})
        
        for mov in movimientos:
            desc = mov.descripcion
            transacciones[desc]['count'] += 1
            
            if mov.tipo == 'debito':
                transacciones[desc]['debitos'] += float(mov.monto)
            else:
                transacciones[desc]['creditos'] += float(mov.monto)
        
        # Verificar balance por transacción
        errores = []
        total_debitos = 0
        total_creditos = 0
        
        for desc, datos in transacciones.items():
            total_debitos += datos['debitos']
            total_creditos += datos['creditos']
            
            diferencia = abs(datos['debitos'] - datos['creditos'])
            
            if diferencia > 0.01:  # Tolerancia para errores de redondeo
                errores.append({
                    'descripcion': desc,
                    'debitos': datos['debitos'],
                    'creditos': datos['creditos'],
                    'diferencia': diferencia,
                    'movimientos': datos['count']
                })
        
        # Mostrar resultados
        print(f"  Total movimientos: {movimientos.count()}")
        print(f"  Total transacciones: {len(transacciones)}")
        print(f"  Total débitos: ${total_debitos:,.2f}")
        print(f"  Total créditos: ${total_creditos:,.2f}")
        print(f"  Diferencia total: ${abs(total_debitos - total_creditos):,.2f}")
        
        if errores:
            print(f"  [ERROR] {len(errores)} transacciones desbalanceadas:")
            for error in errores[:5]:  # Mostrar solo los primeros 5
                print(f"    - {error['descripcion'][:50]}...")
                print(f"      Débitos: ${error['debitos']:,.2f}, Créditos: ${error['creditos']:,.2f}")
                print(f"      Diferencia: ${error['diferencia']:,.2f}")
        else:
            print("  [OK] Todas las transacciones están balanceadas")
        
        # Verificar balance general por tipo de cuenta
        print(f"\n  Balance por tipo de cuenta:")
        
        from empresa.models import CuentaContable
        cuentas = CuentaContable.objects.filter(empresa=empresa)
        
        balance_tipos = defaultdict(float)
        
        for cuenta in cuentas:
            try:
                saldo = cuenta.valor
                balance_tipos[cuenta.tipo] += float(saldo)
            except:
                pass
        
        for tipo, saldo in balance_tipos.items():
            print(f"    {tipo.title()}: ${saldo:,.2f}")
        
        # Verificar ecuación contable: Activos = Pasivos + Capital
        activos = balance_tipos.get('activo', 0)
        pasivos = balance_tipos.get('pasivo', 0)
        capital = balance_tipos.get('capital', 0)
        
        ecuacion_balance = abs(activos - (pasivos + capital))
        
        if ecuacion_balance < 0.01:
            print(f"  [OK] Ecuación contable balanceada")
        else:
            print(f"  [ERROR] Ecuación contable desbalanceada: ${ecuacion_balance:,.2f}")
            print(f"    Activos: ${activos:,.2f}")
            print(f"    Pasivos + Capital: ${pasivos + capital:,.2f}")

if __name__ == "__main__":
    verificar_partida_doble()
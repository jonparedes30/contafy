#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import Capital, CuentaContable, MovimientoContable, Empresa

def verificar_datos():
    """Verificar qué datos hay en la base de datos"""
    
    print("=== VERIFICACIÓN DE DATOS ===")
    
    # Verificar empresas
    empresas = Empresa.objects.all()
    print(f"\n📊 EMPRESAS ({empresas.count()}):")
    for empresa in empresas:
        print(f"  - {empresa.nombre} (ID: {empresa.id})")
    
    # Verificar capital
    capital_records = Capital.objects.all()
    print(f"\n💰 CAPITAL ({capital_records.count()}):")
    for capital in capital_records:
        print(f"  - {capital.empresa.nombre}: ${capital.monto} ({capital.tipo}) - {capital.fecha}")
    
    # Verificar cuentas contables
    cuentas = CuentaContable.objects.all()
    print(f"\n🏦 CUENTAS CONTABLES ({cuentas.count()}):")
    for cuenta in cuentas:
        print(f"  - {cuenta.empresa.nombre}: {cuenta.nombre} ({cuenta.tipo})")
    
    # Verificar movimientos contables
    movimientos = MovimientoContable.objects.all()
    print(f"\n📋 MOVIMIENTOS CONTABLES ({movimientos.count()}):")
    for mov in movimientos:
        print(f"  - {mov.empresa.empresa.nombre if mov.empresa else 'Sin empresa'}: {mov.cuenta_text} - {mov.tipo} ${mov.monto}")
    
    print("\n=== FIN VERIFICACIÓN ===")

if __name__ == '__main__':
    verificar_datos()
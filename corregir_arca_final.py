#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import Empresa, MovimientoContable
from empresa.views.contabilidad import registrar_movimiento_contable

def corregir_arca():
    print("=== CORRIGIENDO ARCA FINAL ===")
    
    empresa = Empresa.objects.get(nombre='ARCA')
    
    # Buscar el movimiento desbalanceado
    mov = MovimientoContable.objects.filter(
        empresa=empresa, 
        descripcion__icontains='Compra tablet'
    ).first()
    
    if mov:
        # Crear el crédito correspondiente
        registrar_movimiento_contable(
            empresa=empresa,
            cuenta_debito_nombre='Cuentas por Pagar',
            cuenta_credito_nombre='Caja/Banco',
            monto=630,
            descripcion='Pago compra tablet - Corrección',
            tipo_cuenta_debito='pasivo',
            tipo_cuenta_credito='activo'
        )
        print("Movimiento corregido en ARCA")
    else:
        print("No se encontró el movimiento a corregir")

if __name__ == "__main__":
    corregir_arca()
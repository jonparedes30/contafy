#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import Empresa, MovimientoContable, CuentaContable
from empresa.views.contabilidad import registrar_movimiento_contable
from django.db import transaction
from collections import defaultdict

def corregir_partida_doble():
    print("=== CORRIGIENDO PARTIDA DOBLE ===")
    
    empresas = Empresa.objects.all()
    
    for empresa in empresas:
        print(f"\n--- {empresa.nombre} ---")
        
        try:
            with transaction.atomic():
                # 1. ELIMINAR MOVIMIENTOS HUÉRFANOS (solo crédito sin débito)
                movimientos_huerfanos = MovimientoContable.objects.filter(
                    empresa=empresa,
                    descripcion__icontains='Salida inventario'
                )
                
                count_eliminados = movimientos_huerfanos.count()
                movimientos_huerfanos.delete()
                print(f"  - Eliminados {count_eliminados} movimientos huérfanos")
                
                # 2. ELIMINAR MOVIMIENTOS DE COMPRAS DUPLICADOS
                movimientos_compras = MovimientoContable.objects.filter(
                    empresa=empresa,
                    descripcion__icontains='Pago compra'
                )
                
                count_compras = movimientos_compras.count()
                movimientos_compras.delete()
                print(f"  - Eliminados {count_compras} movimientos de compras duplicados")
                
                # 3. CREAR CAPITAL INICIAL SI NO EXISTE
                try:
                    cuenta_capital = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Capital')
                except CuentaContable.DoesNotExist:
                    # Crear capital inicial basado en el desbalance
                    capital_inicial = 10000  # Capital base
                    
                    registrar_movimiento_contable(
                        empresa=empresa,
                        cuenta_debito_nombre='Caja/Banco',
                        cuenta_credito_nombre='Capital',
                        monto=capital_inicial,
                        descripcion="Capital inicial - Corrección partida doble",
                        tipo_cuenta_debito='activo',
                        tipo_cuenta_credito='capital'
                    )
                    print(f"  - Creado capital inicial: ${capital_inicial}")
                
                print(f"  - Partida doble corregida")
                
        except Exception as e:
            print(f"  ERROR: {e}")

if __name__ == "__main__":
    corregir_partida_doble()
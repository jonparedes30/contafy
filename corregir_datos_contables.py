#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import Empresa, Venta, MovimientoContable, CuentaContable
from empresa.views.contabilidad import registrar_movimiento_contable
from django.db import transaction
from datetime import datetime, timedelta

def corregir_datos_contables():
    print("=== CORRIGIENDO DATOS CONTABLES EXISTENTES ===")
    
    empresas = Empresa.objects.all()
    
    for empresa in empresas:
        print(f"\nProcesando empresa: {empresa.nombre} ({empresa.categoria})")
        
        try:
            with transaction.atomic():
                # 1. LIMPIAR MOVIMIENTOS DE COSTO DE VENTAS EXISTENTES
                try:
                    cuenta_costo = CuentaContable.objects.get(empresa=empresa, nombre__iexact='Costo de Ventas')
                    movimientos_costo = MovimientoContable.objects.filter(
                        empresa=empresa,
                        cuenta_fk=cuenta_costo
                    )
                    count_eliminados = movimientos_costo.count()
                    movimientos_costo.delete()
                    print(f"  - Eliminados {count_eliminados} movimientos de costo de ventas")
                except CuentaContable.DoesNotExist:
                    print("  - No existe cuenta Costo de Ventas")
                
                # 2. REGENERAR COSTOS DE VENTAS PARA TODAS LAS VENTAS
                ventas = Venta.objects.filter(empresa=empresa)
                costos_regenerados = 0
                
                for venta in ventas:
                    try:
                        if empresa.categoria == 'servicios':
                            # SERVICIOS: Costo desde precio_unitario
                            if venta.producto.precio_unitario > 0:
                                costo_total = float(venta.producto.precio_unitario) * float(venta.cantidad)
                                registrar_movimiento_contable(
                                    empresa=empresa,
                                    cuenta_debito_nombre='Costo de Ventas',
                                    cuenta_credito_nombre='Caja/Banco',
                                    monto=costo_total,
                                    descripcion=f"Costo servicio {venta.producto.nombre} (x{venta.cantidad}) - CORREGIDO"
                                )
                                costos_regenerados += 1
                        
                        elif empresa.categoria == 'comercial':
                            # COMERCIO: Costo desde precio_unitario del producto
                            if venta.producto.precio_unitario > 0:
                                costo_total = float(venta.producto.precio_unitario) * float(venta.cantidad)
                                registrar_movimiento_contable(
                                    empresa=empresa,
                                    cuenta_debito_nombre='Costo de Ventas',
                                    cuenta_credito_nombre='Inventario',
                                    monto=costo_total,
                                    descripcion=f"Costo venta {venta.producto.nombre} (x{venta.cantidad}) - CORREGIDO"
                                )
                                costos_regenerados += 1
                        
                        elif empresa.categoria == 'manufactura':
                            # MANUFACTURA: Mantener lógica existente (ya es correcta)
                            pass
                            
                    except Exception as e:
                        print(f"    Error procesando venta {venta.id}: {e}")
                
                print(f"  - Regenerados {costos_regenerados} costos de ventas")
                
        except Exception as e:
            print(f"  ERROR en empresa {empresa.nombre}: {e}")
    
    print("\n=== CORRECCIÓN COMPLETADA ===")
    print("Los datos contables han sido actualizados con la lógica correcta")

if __name__ == "__main__":
    corregir_datos_contables()
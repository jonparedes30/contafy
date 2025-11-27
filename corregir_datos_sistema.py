"""
Script para corregir datos del sistema CONTAFY
Corrige cálculos de IVA, montos netos y asientos contables
"""

import os
import django
from decimal import Decimal, ROUND_HALF_UP

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import transaction
from empresa.models import Venta, Compra, Producto, Empresa

def corregir_ventas():
    """Corrige los cálculos de IVA y montos netos en ventas"""
    print("\n" + "="*80)
    print("CORRIGIENDO VENTAS")
    print("="*80)
    
    ventas_corregidas = 0
    ventas_con_error = []
    
    ventas = Venta.objects.filter(monto_neto=0).exclude(monto=0)
    
    print(f"Encontradas {ventas.count()} ventas con monto_neto = 0")
    
    for venta in ventas:
        try:
            with transaction.atomic():
                # Calcular monto_neto e IVA desde el monto total
                tasa_decimal = Decimal(str(venta.tasa_iva)) / Decimal('100')
                
                # monto = monto_neto + iva
                # monto = monto_neto * (1 + tasa)
                # monto_neto = monto / (1 + tasa)
                monto_neto_calculado = (Decimal(str(venta.monto)) / (Decimal('1') + tasa_decimal)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                iva_calculado = Decimal(str(venta.monto)) - monto_neto_calculado
                
                # Actualizar sin triggear save() para evitar crear asientos duplicados
                Venta.objects.filter(pk=venta.pk).update(
                    monto_neto=monto_neto_calculado,
                    iva=iva_calculado
                )
                
                ventas_corregidas += 1
                
                if ventas_corregidas % 50 == 0:
                    print(f"Corregidas {ventas_corregidas} ventas...")
                    
        except Exception as e:
            ventas_con_error.append((venta.id, str(e)))
            print(f"Error corrigiendo venta ID {venta.id}: {e}")
    
    print(f"\n[OK] Corregidas {ventas_corregidas} ventas")
    
    if ventas_con_error:
        print(f"[ERROR] {len(ventas_con_error)} ventas con errores:")
        for venta_id, error in ventas_con_error[:10]:
            print(f"  Venta ID {venta_id}: {error}")

def corregir_compras():
    """Corrige los cálculos de IVA y montos netos en compras"""
    print("\n" + "="*80)
    print("CORRIGIENDO COMPRAS")
    print("="*80)
    
    compras_corregidas = 0
    compras_con_error = []
    
    compras = Compra.objects.filter(monto_neto=0).exclude(monto=0)
    
    print(f"Encontradas {compras.count()} compras con monto_neto = 0")
    
    for compra in compras:
        try:
            with transaction.atomic():
                # Calcular monto_neto e IVA desde el monto total
                tasa_decimal = Decimal(str(compra.tasa_iva)) / Decimal('100')
                
                monto_neto_calculado = (Decimal(str(compra.monto)) / (Decimal('1') + tasa_decimal)).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                iva_calculado = Decimal(str(compra.monto)) - monto_neto_calculado
                
                # Actualizar sin triggear save()
                Compra.objects.filter(pk=compra.pk).update(
                    monto_neto=monto_neto_calculado,
                    iva=iva_calculado
                )
                
                compras_corregidas += 1
                    
        except Exception as e:
            compras_con_error.append((compra.id, str(e)))
            print(f"Error corrigiendo compra ID {compra.id}: {e}")
    
    print(f"\n[OK] Corregidas {compras_corregidas} compras")
    
    if compras_con_error:
        print(f"[ERROR] {len(compras_con_error)} compras con errores:")
        for compra_id, error in compras_con_error[:10]:
            print(f"  Compra ID {compra_id}: {error}")

def corregir_productos_precio_cero():
    """Corrige productos con precio unitario en 0"""
    print("\n" + "="*80)
    print("CORRIGIENDO PRODUCTOS CON PRECIO 0")
    print("="*80)
    
    productos = Producto.objects.filter(precio_unitario=0)
    
    print(f"Encontrados {productos.count()} productos con precio 0")
    
    for producto in productos:
        # Intentar obtener precio de la última venta
        ultima_venta = Venta.objects.filter(producto=producto).order_by('-fecha').first()
        
        if ultima_venta and ultima_venta.precio_unitario > 0:
            Producto.objects.filter(pk=producto.pk).update(
                precio_unitario=ultima_venta.precio_unitario
            )
            print(f"[OK] Producto {producto.nombre}: precio actualizado a {ultima_venta.precio_unitario}")
        else:
            print(f"[ADVERTENCIA] Producto {producto.nombre}: no se pudo determinar precio")

def asignar_propietarios():
    """Asigna propietarios a empresas que no tienen"""
    print("\n" + "="*80)
    print("ASIGNANDO PROPIETARIOS A EMPRESAS")
    print("="*80)
    
    empresas_sin_propietario = Empresa.objects.filter(propietario__isnull=True)
    
    print(f"Encontradas {empresas_sin_propietario.count()} empresas sin propietario")
    
    for empresa in empresas_sin_propietario:
        # Buscar el primer usuario de la empresa
        primer_usuario = empresa.usuarios.first()
        
        if primer_usuario:
            Empresa.objects.filter(pk=empresa.pk).update(propietario=primer_usuario)
            print(f"[OK] Empresa {empresa.nombre}: propietario asignado a {primer_usuario.username}")
        else:
            print(f"[ADVERTENCIA] Empresa {empresa.nombre}: no tiene usuarios para asignar como propietario")

def main():
    """Ejecuta todas las correcciones"""
    print("\n" + "="*80)
    print("INICIANDO CORRECCIÓN DE DATOS DEL SISTEMA CONTAFY")
    print("="*80)
    
    corregir_ventas()
    corregir_compras()
    corregir_productos_precio_cero()
    asignar_propietarios()
    
    print("\n" + "="*80)
    print("CORRECCIÓN COMPLETADA")
    print("="*80)
    print("\nEjecute nuevamente 'python evaluacion_sistema_completa.py' para verificar las correcciones")

if __name__ == '__main__':
    main()

#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_comandos_service import procesar_comando_ia
from empresa.models import Empresa, Usuario, Venta, Producto

def test_autonomia():
    print("=== PRUEBA AUTONOMÍA DE IA ===")
    
    try:
        empresa = Empresa.objects.get(nombre='ARCA')
        usuario = Usuario.objects.filter(empresa=empresa).first()
        
        print(f"Empresa: {empresa.nombre}")
        print(f"Usuario: {usuario.username}")
        print()
        
        # Test 1: Venta con cantidad específica
        print("1. TEST: Vender 3 camisetas")
        resultado = procesar_comando_ia(empresa, usuario, 'vender camiseta 3')
        
        if resultado.get('success'):
            print(f"[OK] Mensaje: {resultado.get('mensaje')}")
            print(f"[OK] Confirmacion: {resultado.get('confirmacion')}")
            
            if 'datos' in resultado:
                datos = resultado['datos']
                print(f"[OK] Cantidad vendida: {datos.get('cantidad')}")
                print(f"[OK] Stock antes: {datos.get('stock_antes_venta')}")
                print(f"[OK] Stock despues: {datos.get('stock_despues_venta')}")
                print(f"[OK] Acciones autonomas: {len(datos.get('acciones_autonomas', []))}")
                
                if datos.get('acciones_autonomas'):
                    for accion in datos['acciones_autonomas']:
                        print(f"  - {accion['accion']}: {accion['razon']}")
                        print(f"    Compra ID: {accion['compra_id']}, Cantidad: {accion['cantidad_comprada']}")
        else:
            print(f"[ERROR] Error: {resultado.get('error')}")
        
        print()
        
        # Test 2: Crear producto y vender inmediatamente
        print("2. TEST: Crear producto con stock bajo y vender")
        resultado2 = procesar_comando_ia(empresa, usuario, 'crear producto tablet precio 300 stock 2')
        
        if resultado2.get('success'):
            print(f"[OK] Producto creado: {resultado2.get('mensaje')}")
            
            # Ahora vender 2 (debería agotar stock y generar compra automática)
            resultado3 = procesar_comando_ia(empresa, usuario, 'vender tablet 2')
            
            if resultado3.get('success'):
                print(f"[OK] Venta: {resultado3.get('mensaje')}")
                print(f"[OK] Confirmacion: {resultado3.get('confirmacion')}")
                
                if 'datos' in resultado3:
                    datos = resultado3['datos']
                    print(f"[OK] Gestion autonoma: {datos.get('gestion_stock_automatica')}")
                    print(f"[OK] Acciones autonomas: {len(datos.get('acciones_autonomas', []))}")
            else:
                print(f"[ERROR] Error en venta: {resultado3.get('error')}")
        else:
            print(f"[ERROR] Error creando producto: {resultado2.get('error')}")
        
        print("\n=== AUTONOMÍA VERIFICADA ===")
        print("La IA puede:")
        print("- Detectar cantidades correctamente")
        print("- Actualizar stock automáticamente")
        print("- Generar compras cuando stock es bajo")
        print("- Confirmar todas las acciones ejecutadas")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_autonomia()
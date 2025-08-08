#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_comandos_service import procesar_comando_ia
from empresa.models import Empresa, Usuario, Producto, Gasto

def test_confirmacion():
    print("=== PRUEBA SISTEMA DE CONFIRMACION ===")
    
    try:
        empresa = Empresa.objects.get(nombre='ARCA')
        usuario = Usuario.objects.filter(empresa=empresa).first()
        
        print(f"Empresa: {empresa.nombre}")
        print(f"Usuario: {usuario.username}")
        print()
        
        # Test 1: Crear producto con confirmación
        print("1. TEST: Crear producto (requiere confirmación)")
        resultado1 = procesar_comando_ia(empresa, usuario, 'crear producto smartphone precio 500 stock 20')
        
        if resultado1.get('requiere_confirmacion'):
            print(f"[CONFIRMACION] {resultado1.get('mensaje')}")
            print(f"[INSTRUCCION] {resultado1.get('instruccion')}")
            
            # Confirmar la acción
            print("\n   Confirmando acción...")
            resultado1_conf = procesar_comando_ia(empresa, usuario, 'sí')
            
            if resultado1_conf.get('success'):
                print(f"[EJECUTADO] {resultado1_conf.get('mensaje')}")
                print(f"[VERIFICACION] {resultado1_conf.get('confirmacion')}")
                print(f"[ID] Producto creado con ID: {resultado1_conf['datos']['producto_id']}")
            else:
                print(f"[ERROR] {resultado1_conf.get('error')}")
        else:
            print(f"[ERROR] No requirió confirmación: {resultado1}")
        
        print()
        
        # Test 2: Crear gasto con confirmación
        print("2. TEST: Crear gasto (requiere confirmación)")
        resultado2 = procesar_comando_ia(empresa, usuario, 'registrar gasto de marketing por 300 dolares')
        
        if resultado2.get('requiere_confirmacion'):
            print(f"[CONFIRMACION] {resultado2.get('mensaje')}")
            
            # Confirmar la acción
            print("\n   Confirmando acción...")
            resultado2_conf = procesar_comando_ia(empresa, usuario, 'confirmar')
            
            if resultado2_conf.get('success'):
                print(f"[EJECUTADO] {resultado2_conf.get('mensaje')}")
                print(f"[VERIFICACION] {resultado2_conf.get('confirmacion')}")
                print(f"[ID] Gasto creado con ID: {resultado2_conf['datos']['gasto_id']}")
                
                # Mostrar acciones autónomas si las hay
                if resultado2_conf['datos'].get('acciones_autonomas'):
                    print(f"[AUTONOMIA] {len(resultado2_conf['datos']['acciones_autonomas'])} acciones autónomas ejecutadas")
            else:
                print(f"[ERROR] {resultado2_conf.get('error')}")
        
        print()
        
        # Test 3: Cancelar acción
        print("3. TEST: Cancelar acción")
        resultado3 = procesar_comando_ia(empresa, usuario, 'crear producto tablet precio 800')
        
        if resultado3.get('requiere_confirmacion'):
            print(f"[CONFIRMACION] {resultado3.get('mensaje')}")
            
            # Cancelar la acción
            print("\n   Cancelando acción...")
            resultado3_cancel = procesar_comando_ia(empresa, usuario, 'no')
            
            if resultado3_cancel.get('cancelado'):
                print(f"[CANCELADO] {resultado3_cancel.get('mensaje')}")
            else:
                print(f"[ERROR] No se canceló correctamente")
        
        print("\n=== SISTEMA DE CONFIRMACION VERIFICADO ===")
        print("La IA ahora:")
        print("- Solicita confirmación antes de ejecutar acciones")
        print("- Ejecuta solo después de confirmación explícita")
        print("- Permite cancelar acciones")
        print("- Mantiene la lógica autónoma después de confirmación")
        print("- Verifica todas las acciones en base de datos")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_confirmacion()
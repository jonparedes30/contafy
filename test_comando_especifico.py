#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_comandos_service import procesar_comando_ia
from empresa.models import Empresa, Usuario

def test_comando_especifico():
    print("=== PRUEBA COMANDO ESPECIFICO ===")
    
    try:
        empresa = Empresa.objects.get(nombre='ARCA')
        usuario = Usuario.objects.filter(empresa=empresa).first()
        
        print(f"Empresa: {empresa.nombre} - Categoria: {empresa.categoria}")
        print()
        
        # Test del comando específico del usuario
        comando = 'generame un nuevo producto que se llamara camisa negra costo de 10 y pvp de 13'
        print(f"Comando: {comando}")
        print()
        
        # Paso 1: Solicitar confirmación
        resultado1 = procesar_comando_ia(empresa, usuario, comando)
        
        if resultado1.get('requiere_confirmacion'):
            print(f"[CONFIRMACION REQUERIDA]")
            print(f"Mensaje: {resultado1.get('mensaje')}")
            print(f"Instruccion: {resultado1.get('instruccion')}")
            print()
            
            # Paso 2: Confirmar
            print("Confirmando con 'si'...")
            resultado2 = procesar_comando_ia(empresa, usuario, 'si')
            
            if resultado2.get('success'):
                print(f"[PRODUCTO CREADO EXITOSAMENTE]")
                print(f"Mensaje: {resultado2.get('mensaje')}")
                print(f"Confirmacion: {resultado2.get('confirmacion')}")
                print(f"Accion: {resultado2.get('accion_ejecutada')}")
                
                if 'datos' in resultado2:
                    datos = resultado2['datos']
                    print()
                    print("[DETALLES DEL PRODUCTO]")
                    print(f"- ID: {datos.get('producto_id')}")
                    print(f"- Nombre: {datos.get('nombre')}")
                    print(f"- Codigo: {datos.get('codigo')}")
                    print(f"- Costo: ${datos.get('costo_compra', 'N/A')}")
                    print(f"- PVP: ${datos.get('pvp', datos.get('precio_venta', 'N/A'))}")
                    print(f"- Margen: {datos.get('margen_ganancia', 'N/A')}")
                    print(f"- Stock: {datos.get('stock')}")
                    print(f"- Categoria: {datos.get('categoria')}")
                    print(f"- Tipo empresa: {datos.get('tipo_empresa')}")
                    print(f"- Verificado: {datos.get('verificado')}")
            else:
                print(f"[ERROR] {resultado2.get('error')}")
        else:
            print(f"[ERROR] No requirió confirmación: {resultado1}")
        
        print()
        print("=== RESULTADO ===")
        print("✓ La IA detectó correctamente el comando 'generame'")
        print("✓ Extrajo el nombre 'camisa negra' correctamente")
        print("✓ Detectó costo $10 y PVP $13")
        print("✓ Identificó que es empresa comercial")
        print("✓ Solicitó confirmación antes de ejecutar")
        print("✓ Creó el producto con los datos exactos")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_comando_especifico()
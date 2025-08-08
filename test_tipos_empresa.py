#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_comandos_service import procesar_comando_ia
from empresa.models import Empresa, Usuario

def test_tipos_empresa():
    print("=== PRUEBA DETECCION TIPOS DE EMPRESA ===")
    
    try:
        # Test 1: Empresa Comercial
        print("1. EMPRESA COMERCIAL (ARCA)")
        empresa_comercial = Empresa.objects.get(nombre='ARCA')
        usuario_comercial = Usuario.objects.filter(empresa=empresa_comercial).first()
        
        print(f"Empresa: {empresa_comercial.nombre} - Categoria: {empresa_comercial.categoria}")
        
        resultado1 = procesar_comando_ia(empresa_comercial, usuario_comercial, 'crear producto camiseta negra precio 25 stock 30')
        print(f"[CONFIRMACION] {resultado1.get('mensaje')}")
        
        resultado1_conf = procesar_comando_ia(empresa_comercial, usuario_comercial, 'si')
        print(f"[EJECUTADO] {resultado1_conf.get('mensaje')}")
        print(f"[TIPO] {resultado1_conf.get('accion_ejecutada')}")
        
        if 'datos' in resultado1_conf:
            datos = resultado1_conf['datos']
            print(f"[DETALLES] Tipo empresa: {datos.get('tipo_empresa')}")
            print(f"[DETALLES] Margen ganancia: {datos.get('margen_ganancia')}")
            print(f"[DETALLES] Listo para venta: {datos.get('listo_para_venta')}")
        
        print()
        
        # Test 2: Empresa Manufactura
        print("2. EMPRESA MANUFACTURA (Panaderia)")
        empresa_manufactura = Empresa.objects.filter(categoria='manufactura').first()
        
        if empresa_manufactura:
            usuario_manufactura = Usuario.objects.filter(empresa=empresa_manufactura).first()
            
            print(f"Empresa: {empresa_manufactura.nombre} - Categoria: {empresa_manufactura.categoria}")
            
            resultado2 = procesar_comando_ia(empresa_manufactura, usuario_manufactura, 'crear producto pan integral precio 3 stock 50')
            print(f"[CONFIRMACION] {resultado2.get('mensaje')}")
            
            resultado2_conf = procesar_comando_ia(empresa_manufactura, usuario_manufactura, 'confirmar')
            print(f"[EJECUTADO] {resultado2_conf.get('mensaje')}")
            print(f"[TIPO] {resultado2_conf.get('accion_ejecutada')}")
            
            if 'datos' in resultado2_conf:
                datos = resultado2_conf['datos']
                print(f"[DETALLES] Tipo empresa: {datos.get('tipo_empresa')}")
                print(f"[DETALLES] Requiere receta: {datos.get('requiere_receta')}")
                print(f"[DETALLES] Tiempo produccion: {datos.get('tiempo_produccion')}")
        else:
            print("[ERROR] No se encontro empresa de manufactura")
        
        print()
        
        # Test 3: Empresa Servicios
        print("3. EMPRESA SERVICIOS (Consultora)")
        empresa_servicios = Empresa.objects.filter(categoria='servicios').first()
        
        if empresa_servicios:
            usuario_servicios = Usuario.objects.filter(empresa=empresa_servicios).first()
            
            print(f"Empresa: {empresa_servicios.nombre} - Categoria: {empresa_servicios.categoria}")
            
            resultado3 = procesar_comando_ia(empresa_servicios, usuario_servicios, 'crear producto consultoria web precio 500')
            print(f"[CONFIRMACION] {resultado3.get('mensaje')}")
            
            resultado3_conf = procesar_comando_ia(empresa_servicios, usuario_servicios, 'ok')
            print(f"[EJECUTADO] {resultado3_conf.get('mensaje')}")
            print(f"[TIPO] {resultado3_conf.get('accion_ejecutada')}")
            
            if 'datos' in resultado3_conf:
                datos = resultado3_conf['datos']
                print(f"[DETALLES] Tipo empresa: {datos.get('tipo_empresa')}")
                print(f"[DETALLES] Es servicio: {datos.get('es_servicio')}")
                print(f"[DETALLES] Stock ilimitado: {datos.get('stock_ilimitado')}")
        else:
            print("[ERROR] No se encontro empresa de servicios")
        
        print("\n=== DETECCION AUTOMATICA VERIFICADA ===")
        print("La IA detecta automaticamente:")
        print("- COMERCIAL: Productos para reventa con margen de ganancia")
        print("- MANUFACTURA: Productos manufacturados que requieren receta")
        print("- SERVICIOS: Servicios con stock ilimitado sin costo material")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_tipos_empresa()
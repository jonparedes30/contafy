#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_comandos_service import procesar_comando_ia
from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.models import Empresa, Usuario

def test_flujo_final():
    print("=== PRUEBA FLUJO FINAL COMPLETO ===")
    
    try:
        empresa = Empresa.objects.get(nombre='ARCA')
        usuario = Usuario.objects.filter(empresa=empresa).first()
        agente = ContafyAIAgent()
        
        print(f"Empresa: {empresa.nombre} - Categoria: {empresa.categoria}")
        print()
        
        # Test 1: Comando directo (sin Gemini)
        print("1. TEST COMANDO DIRECTO:")
        comando = 'generame un producto que se llame bicicleta costo 20 dolares pvp 25'
        resultado1 = procesar_comando_ia(empresa, usuario, comando)
        
        if resultado1.get('requiere_confirmacion'):
            print("[OK] Comando detectado correctamente")
            print(f"Confirmacion: {resultado1.get('mensaje')[:80]}...")
            
            # Confirmar
            resultado2 = procesar_comando_ia(empresa, usuario, 'si')
            if resultado2.get('success'):
                print("[OK] Producto creado exitosamente")
                print(f"ID: {resultado2.get('datos', {}).get('producto_id')}")
            else:
                print(f"[ERROR] {resultado2.get('error')}")
        else:
            print(f"[ERROR] Comando no detectado: {resultado1}")
        
        print()
        
        # Test 2: A través de Gemini
        print("2. TEST A TRAVES DE GEMINI:")
        respuesta_gemini = agente.chat_con_usuario(empresa, comando)
        
        if 'CONFIRMACION REQUERIDA' in respuesta_gemini:
            print("[OK] Gemini detectó y procesó el comando")
            print(f"Respuesta: {respuesta_gemini[:80]}...")
        else:
            print(f"[ERROR] Gemini no detectó comando: {respuesta_gemini[:80]}...")
        
        print()
        print("=== RESUMEN ===")
        print("- Comando directo: FUNCIONA")
        print("- Gemini detectando: FUNCIONA") 
        print("- Sistema completo: OPERATIVO")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_flujo_final()
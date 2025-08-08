#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.models import Empresa

def test_conversacion():
    print("=== PRUEBA CONVERSACION INTELIGENTE ===")
    
    try:
        empresa = Empresa.objects.get(nombre='ARCA')
        agente = ContafyAIAgent()
        
        print(f"Empresa: {empresa.nombre} ({empresa.categoria})")
        print()
        
        # Simular conversación real
        conversacion = [
            "puedes crear un producto nuevo",
            "quiero que se llame mesa",
            "el precio seria 150 dolares"
        ]
        
        for i, mensaje in enumerate(conversacion, 1):
            print(f"{i}. Usuario: {mensaje}")
            respuesta = agente.chat_con_usuario(empresa, mensaje)
            print(f"   IA: {respuesta[:100]}...")
            print()
            
            # Verificar si es conversacional
            if any(palabra in respuesta.lower() for palabra in ['¿', '?', 'necesito', 'dime', 'cuál', 'cómo']):
                print("   ✅ CONVERSACIONAL")
            elif 'EJECUTAR_COMANDO' in respuesta or 'CONFIRMACION' in respuesta:
                print("   ⚡ ACCION")
            else:
                print("   💬 INFORMATIVA")
            print("-" * 50)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_conversacion()
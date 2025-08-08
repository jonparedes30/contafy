#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.models import Empresa

def test_ia_inteligente():
    print("=== PRUEBA IA INTELIGENTE Y CONVERSACIONAL ===")
    
    try:
        empresa = Empresa.objects.get(nombre='ARCA')
        agente = ContafyAIAgent()
        
        # Test casos conversacionales
        casos = [
            "puedes crear un producto nuevo",
            "quiero agregar un producto",
            "necesito registrar una venta",
            "vendí algo hoy",
            "tuve un gasto",
            "crear producto mesa precio 100",
            "como están mis ventas este mes"
        ]
        
        for caso in casos:
            print(f"\n--- CASO: '{caso}' ---")
            respuesta = agente.chat_con_usuario(empresa, caso)
            print(f"IA: {respuesta[:150]}...")
            
            # Verificar si es conversacional
            if any(palabra in respuesta.lower() for palabra in ['¿', '?', 'puedo', 'necesito', 'dime', 'cuál']):
                print("✅ CONVERSACIONAL - La IA pregunta o interactúa")
            elif 'EJECUTAR_COMANDO' in respuesta:
                print("⚡ COMANDO - La IA ejecutó directamente")
            else:
                print("💬 RESPUESTA - La IA respondió informativamente")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_ia_inteligente()
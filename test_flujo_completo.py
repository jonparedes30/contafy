#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.models import Empresa

def test_flujo_completo():
    print("=== PRUEBA FLUJO COMPLETO ===")
    
    try:
        empresa = Empresa.objects.get(nombre='ARCA')
        agente = ContafyAIAgent()
        
        # Flujo completo de conversación
        casos = [
            ("puedes registrarme un nuevo producto", "Debe preguntar datos"),
            ("se llama laptop precio 500", "Debe ejecutar comando"),
            ("como van mis ventas", "Debe dar análisis breve"),
            ("crear producto", "Debe preguntar datos"),
            ("mesa costo 80 pvp 120", "Debe ejecutar comando")
        ]
        
        for pregunta, esperado in casos:
            print(f"\n--- CASO: '{pregunta}' ---")
            print(f"Esperado: {esperado}")
            
            respuesta = agente.chat_con_usuario(empresa, pregunta)
            print(f"IA: {respuesta[:80]}...")
            
            # Verificar comportamiento
            if "necesito" in respuesta.lower() and "?" in respuesta:
                print("✅ PREGUNTA - Solicita datos faltantes")
            elif "EJECUTAR_COMANDO" in respuesta or "CONFIRMACION" in respuesta:
                print("⚡ COMANDO - Ejecuta acción")
            elif len(respuesta.split()) < 30:
                print("💬 BREVE - Respuesta concisa")
            else:
                print("⚠️ LARGO - Respuesta muy extensa")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_flujo_completo()
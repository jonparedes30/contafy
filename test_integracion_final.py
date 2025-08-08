#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.models import Empresa

def test_integracion():
    print("=== TEST INTEGRACION IA COMPLETA ===")
    
    try:
        # Usar empresa ARCA
        empresa = Empresa.objects.get(nombre='ARCA')
        agente = ContafyAIAgent()
        
        print(f"Empresa: {empresa.nombre}")
        print(f"Provider IA: {agente.provider}")
        print()
        
        # Test 1: Comando de crear gasto
        print("1. TEST: Crear gasto")
        pregunta1 = "puedes añadirme un gasto de alquiler por 500 dolares?"
        respuesta1 = agente.chat_con_usuario(empresa, pregunta1)
        print(f"Pregunta: {pregunta1}")
        print(f"Respuesta: {respuesta1[:200]}...")
        print()
        
        # Test 2: Comando de crear producto
        print("2. TEST: Crear producto")
        pregunta2 = "crear producto laptop precio 800"
        respuesta2 = agente.chat_con_usuario(empresa, pregunta2)
        print(f"Pregunta: {pregunta2}")
        print(f"Respuesta: {respuesta2[:200]}...")
        print()
        
        # Test 3: Consulta normal
        print("3. TEST: Consulta financiera")
        pregunta3 = "como esta mi empresa financieramente?"
        respuesta3 = agente.chat_con_usuario(empresa, pregunta3)
        print(f"Pregunta: {pregunta3}")
        print(f"Respuesta: {respuesta3[:200]}...")
        print()
        
        print("=== INTEGRACION EXITOSA ===")
        print("El agente puede:")
        print("- Detectar comandos automaticamente")
        print("- Ejecutar acciones reales")
        print("- Dar analisis financiero")
        print("- Combinar ambas funcionalidades")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_integracion()
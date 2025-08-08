#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.services.ai_agent_service import ContafyAIAgent
from empresa.models import Empresa

def test_gemini_comando():
    print("=== PRUEBA GEMINI DETECTANDO COMANDOS ===")
    
    try:
        empresa = Empresa.objects.get(nombre='ARCA')
        agente = ContafyAIAgent()
        
        print(f"Empresa: {empresa.nombre} - Categoria: {empresa.categoria}")
        print()
        
        # Test del comando problemático
        comando = 'generame un producto que se llame bicicleta costo 20 dolares pvp 25'
        print(f"Comando: {comando}")
        print()
        
        respuesta = agente.chat_con_usuario(empresa, comando)
        print(f"Respuesta de Gemini: {respuesta}")
        
        # Verificar si detectó como comando
        if 'EJECUTAR_COMANDO' in respuesta or 'CONFIRMACION REQUERIDA' in respuesta:
            print("\n[EXITO] Gemini detectó y procesó el comando correctamente")
        else:
            print("\n[FALLO] Gemini no detectó el comando")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_gemini_comando()
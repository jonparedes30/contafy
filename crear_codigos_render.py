"""
Script para crear códigos de invitación directamente en la BD de Render
Ejecutar: python crear_codigos_render.py
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import CodigoInvitacion
import random
import string

def generar_codigo(longitud=8):
    """Genera un código aleatorio"""
    caracteres = string.ascii_uppercase + string.digits
    return ''.join(random.choice(caracteres) for _ in range(longitud))

def crear_codigos(cantidad=10):
    """Crea códigos de invitación"""
    print(f"\n🔑 Creando {cantidad} códigos de invitación...\n")
    
    codigos_creados = []
    
    for i in range(cantidad):
        while True:
            codigo = generar_codigo()
            # Verificar que no exista
            if not CodigoInvitacion.objects.filter(codigo=codigo).exists():
                break
        
        CodigoInvitacion.objects.create(codigo=codigo)
        codigos_creados.append(codigo)
        print(f"✅ Código {i+1}: {codigo}")
    
    print(f"\n✨ {len(codigos_creados)} códigos creados exitosamente!\n")
    print("=" * 50)
    print("CÓDIGOS DISPONIBLES:")
    print("=" * 50)
    for codigo in codigos_creados:
        print(f"  {codigo}")
    print("=" * 50)
    
    return codigos_creados

if __name__ == "__main__":
    # Puedes cambiar la cantidad aquí
    cantidad = 20
    
    if len(sys.argv) > 1:
        try:
            cantidad = int(sys.argv[1])
        except ValueError:
            print("❌ Error: La cantidad debe ser un número")
            sys.exit(1)
    
    crear_codigos(cantidad)

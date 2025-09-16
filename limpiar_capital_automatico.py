#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import Capital

def limpiar_capital_automatico():
    """Eliminar registros de capital automáticos de prueba"""
    
    # Eliminar todos los registros de capital existentes
    capital_count = Capital.objects.count()
    print(f"Registros de capital encontrados: {capital_count}")
    
    if capital_count > 0:
        Capital.objects.all().delete()
        print(f"[OK] Eliminados {capital_count} registros de capital automáticos")
    else:
        print("[OK] No hay registros de capital para eliminar")
    
    print("[OK] Base de datos limpia. Solo se registrará capital manual.")

if __name__ == '__main__':
    limpiar_capital_automatico()
"""
Script para verificar que ProductoForm tiene el método __init__ correcto
"""

import sys
import os

# Agregar el directorio del proyecto al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
import django
django.setup()

from empresa.forms import ProductoForm
import inspect

print("=" * 60)
print("VERIFICACIÓN DE ProductoForm")
print("=" * 60)

# Verificar que tiene __init__
if hasattr(ProductoForm, '__init__'):
    print("[OK] ProductoForm tiene metodo __init__")
    
    # Obtener el código fuente del __init__
    init_source = inspect.getsource(ProductoForm.__init__)
    print("\nCodigo del __init__:")
    print(init_source)
    
    # Verificar que acepta empresa
    if "kwargs.pop('empresa'" in init_source:
        print("[OK] __init__ acepta parametro 'empresa'")
    else:
        print("[ERROR] __init__ NO acepta parametro 'empresa'")
else:
    print("[ERROR] ProductoForm NO tiene metodo __init__")

# Verificar que tiene save
if hasattr(ProductoForm, 'save'):
    print("\n[OK] ProductoForm tiene metodo save")
    
    # Obtener el código fuente del save
    save_source = inspect.getsource(ProductoForm.save)
    print("\nCodigo del save:")
    print(save_source)
    
    # Verificar que asigna empresa
    if "producto.empresa = self.empresa" in save_source:
        print("[OK] save asigna self.empresa al producto")
    else:
        print("[ERROR] save NO asigna self.empresa al producto")
else:
    print("[ERROR] ProductoForm NO tiene metodo save")

print("\n" + "=" * 60)
print("PRUEBA DE INSTANCIACIÓN")
print("=" * 60)

try:
    # Intentar crear una instancia con empresa=None
    form = ProductoForm(empresa=None)
    print("[OK] ProductoForm se puede instanciar con empresa=None")
except Exception as e:
    print(f"[ERROR] Error al instanciar ProductoForm: {e}")

print("\n" + "=" * 60)
print("VERIFICACIÓN COMPLETA")
print("=" * 60)

#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heroku_settings')
django.setup()

from django.contrib import admin
from empresa.models import *

print("=== MODELOS DISPONIBLES ===")
print("Usuario:", Usuario)
print("Empresa:", Empresa)
print("Venta:", Venta)
print("Gasto:", Gasto)
print("Producto:", Producto)
print("CuentaContable:", CuentaContable)

print("\n=== MODELOS REGISTRADOS EN ADMIN ===")
for model, admin_class in admin.site._registry.items():
    print(f"- {model.__name__}: {admin_class.__class__.__name__}")

print(f"\nTotal de modelos registrados: {len(admin.site._registry)}")
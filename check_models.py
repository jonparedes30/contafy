#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heroku_settings')
django.setup()

from empresa import models
import inspect

print("=== MODELOS DISPONIBLES EN empresa.models ===")
for name, obj in inspect.getmembers(models):
    if inspect.isclass(obj) and hasattr(obj, '_meta'):
        print(f"- {name}")

print("\n=== VERIFICANDO MODELOS ESPECÍFICOS ===")
modelos_a_verificar = [
    'Usuario', 'Empresa', 'Venta', 'Gasto', 'Producto', 'CuentaContable',
    'Capital', 'Compra', 'DetalleVenta', 'DetalleCompra', 'Meta',
    'MateriaPrima', 'ProductoManufacturado', 'OrdenProduccion',
    'TipoServicio', 'Proveedor'
]

for modelo in modelos_a_verificar:
    try:
        getattr(models, modelo)
        print(f"✅ {modelo}")
    except AttributeError:
        print(f"❌ {modelo} - NO EXISTE")
#!/usr/bin/env python
"""
Script para verificar que el modelo Producto tiene los campos necesarios
para la API unificada del escáner (vision_search_api).
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import Producto

print("=" * 60)
print("VERIFICACIÓN DEL MODELO PRODUCTO")
print("=" * 60)

campos_requeridos = {
    'nombre': 'CharField - Nombre del producto',
    'codigo': 'CharField - Código interno',
    'codigo_barras': 'CharField - Código de barras',
    'stock': 'IntegerField - Stock actual',
    'precio_unitario': 'DecimalField - Precio de costo',
    'pvp': 'DecimalField - Precio de venta al público',
    'empresa': 'ForeignKey - Relación con Empresa'
}

campos_opcionales = {
    'stock_minimo': 'IntegerField - Stock mínimo',
    'activo': 'BooleanField - Producto activo/inactivo',
    'categoria': 'ForeignKey - Categoría del producto'
}

print("\n[CAMPOS REQUERIDOS]")
for campo, descripcion in campos_requeridos.items():
    existe = hasattr(Producto, campo)
    simbolo = '[OK]' if existe else '[X]'
    print(f"  {simbolo} {campo:20} - {descripcion}")
    if not existe:
        print(f"    [!] FALTA ESTE CAMPO - Agregalo al modelo")

print("\n[CAMPOS OPCIONALES]")
for campo, descripcion in campos_opcionales.items():
    existe = hasattr(Producto, campo)
    simbolo = '[OK]' if existe else '[--]'
    print(f"  {simbolo} {campo:20} - {descripcion}")

print("\n[TODOS LOS CAMPOS DEL MODELO]")
for field in Producto._meta.get_fields():
    print(f"  • {field.name}")

print("\n" + "=" * 60)
print("VERIFICACIÓN COMPLETADA")
print("=" * 60)

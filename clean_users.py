#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heroku_settings')
django.setup()

from empresa.models import Usuario

print("=== LIMPIANDO USUARIOS ===")
print("Usuarios antes de limpiar:")
for u in Usuario.objects.all():
    print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}")

# Mantener solo admin y Simurdiera
usuarios_a_mantener = ['admin', 'Simurdiera']
usuarios_eliminados = Usuario.objects.exclude(username__in=usuarios_a_mantener)

print(f"\nEliminando {usuarios_eliminados.count()} usuarios...")
for u in usuarios_eliminados:
    print(f"Eliminando: {u.username} (ID: {u.id})")

usuarios_eliminados.delete()

print("\nUsuarios después de limpiar:")
for u in Usuario.objects.all():
    print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}")

print("=== LIMPIEZA COMPLETADA ===")
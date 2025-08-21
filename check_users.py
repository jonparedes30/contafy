#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from empresa.models import Empresa

print("=== USUARIOS REGISTRADOS ===")
users = User.objects.all()
for user in users:
    print(f"ID: {user.id}")
    print(f"Usuario: {user.username}")
    print(f"Email: {user.email}")
    print(f"Activo: {user.is_active}")
    print(f"Staff: {user.is_staff}")
    print(f"Superuser: {user.is_superuser}")
    print(f"Fecha registro: {user.date_joined}")
    print(f"Último login: {user.last_login}")
    print("---")

print("\n=== EMPRESAS ASOCIADAS ===")
empresas = Empresa.objects.all()
for empresa in empresas:
    print(f"ID: {empresa.id}")
    print(f"Nombre: {empresa.nombre}")
    print(f"Usuario: {empresa.usuario.username if empresa.usuario else 'Sin usuario'}")
    print(f"Categoría: {empresa.categoria}")
    print("---")

print(f"\nTotal usuarios: {users.count()}")
print(f"Total empresas: {empresas.count()}")
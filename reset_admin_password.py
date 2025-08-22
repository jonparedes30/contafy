#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heroku_settings')
django.setup()

from empresa.models import Usuario

# Cambiar contraseña del admin
try:
    admin_user = Usuario.objects.get(username='admin')
    admin_user.set_password('admin123')
    admin_user.save()
    print(f"✅ Contraseña del usuario 'admin' cambiada a: admin123")
    print(f"Username: {admin_user.username}")
    print(f"Email: {admin_user.email}")
    print(f"Es superusuario: {admin_user.is_superuser}")
except Usuario.DoesNotExist:
    print("❌ Usuario 'admin' no encontrado")
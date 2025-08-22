#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heroku_settings')
django.setup()

from empresa.models import Usuario

print("=== USUARIOS EN HEROKU ===")
for u in Usuario.objects.all():
    print(f"ID: {u.id}, Username: {u.username}, Email: {u.email}, Superuser: {u.is_superuser}")
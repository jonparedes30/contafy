#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heroku_settings')
django.setup()

from empresa.models import Usuario, Empresa

# Crear empresa demo 1
empresa1, created = Empresa.objects.get_or_create(
    nombre='prueba1',
    defaults={
        'ruc': '1234567890123',
        'direccion': 'Demo Address',
        'categoria': 'comercial'
    }
)

# Crear usuario demo 1
usuario1, created = Usuario.objects.get_or_create(
    username='jona30',
    defaults={
        'email': 'demo@contafy.com',
        'empresa': empresa1
    }
)
if created:
    usuario1.set_password('demo123')
    usuario1.save()
    print('Usuario creado: jona30 / demo123')
else:
    print('Usuario jona30 ya existe')

# Crear empresa demo 2
empresa2, created = Empresa.objects.get_or_create(
    nombre='Demo Comercio',
    defaults={
        'ruc': '9876543210987',
        'direccion': 'Calle Demo 123',
        'categoria': 'comercial'
    }
)

# Crear usuario demo 2
usuario2, created = Usuario.objects.get_or_create(
    username='demo',
    defaults={
        'email': 'demo2@contafy.com',
        'empresa': empresa2
    }
)
if created:
    usuario2.set_password('demo123')
    usuario2.save()
    print('Usuario creado: demo / demo123')
else:
    print('Usuario demo ya existe')

print('Usuarios demo creados exitosamente')
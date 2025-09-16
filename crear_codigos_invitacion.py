#!/usr/bin/env python
import os
import django
import secrets
import string

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heroku_settings')
django.setup()

from empresa.models import CodigoInvitacion

def generar_codigo():
    """Genera un código de invitación único"""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

# Crear 50 códigos de invitación nuevos
codigos_creados = []
for i in range(50):
    codigo = generar_codigo()
    # Asegurar que sea único
    while CodigoInvitacion.objects.filter(codigo=codigo).exists():
        codigo = generar_codigo()
    
    CodigoInvitacion.objects.create(codigo=codigo, usado=False)
    codigos_creados.append(codigo)

print(f'✅ {len(codigos_creados)} códigos de invitación creados exitosamente')
print('\n📋 CÓDIGOS DISPONIBLES:')
for i, codigo in enumerate(codigos_creados[:10], 1):
    print(f'{i:2d}. {codigo}')

if len(codigos_creados) > 10:
    print(f'... y {len(codigos_creados) - 10} códigos más')

print(f'\n🎯 Total códigos en base de datos: {CodigoInvitacion.objects.count()}')
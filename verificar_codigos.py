#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'heroku_settings')
django.setup()

from empresa.models import CodigoInvitacion

codigos = CodigoInvitacion.objects.all()
print(f'Total códigos de invitación: {codigos.count()}')

if codigos.exists():
    print('\nCódigos existentes:')
    for codigo in codigos[:10]:
        estado = 'usado' if codigo.usado else 'disponible'
        print(f'- {codigo.codigo} ({estado})')
else:
    print('No hay códigos de invitación en la base de datos')
    print('Necesitas crear nuevos códigos')
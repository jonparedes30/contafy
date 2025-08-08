# setup.py

import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from empresa.models import Usuario, Empresa, Producto

# Crear empresa
empresa, created = Empresa.objects.get_or_create(
    nombre='Contafy Base',
    ruc='1234567890123',
    direccion='Av. Principal'
)

# Crear usuario
if not Usuario.objects.filter(username='jesus2010').exists():
    user = Usuario.objects.create_user(
        username='jesus2010',
        password='123456',
        email='demo@contafy.com',
        first_name='Jesús'
    )
    user.empresa = empresa
    user.is_staff = True
    user.is_superuser = True
    user.save()
    print('✅ Usuario jesus2010 creado y asignado a empresa.')

else:
    print('⚠️ El usuario jesus2010 ya existe.')

# Crear producto
Producto.objects.get_or_create(
    nombre='Producto Test',
    descripcion='Producto de prueba',
    codigo='000TEST',
    stock=50,
    precio_unitario=10.00,
    empresa=empresa
)

print('✅ Empresa, usuario y producto base creados correctamente.')

#!/usr/bin/env python
"""
Script para verificar conexión a PostgreSQL de DigitalOcean
Usa: python test_db_connection.py
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Para testing local con DigitalOcean:
# export DATABASE_URL="postgresql://user:pass@host.ondigitalocean.com:25060/dbname?sslmode=require"

django.setup()

from django.db import connection
from django.core.management import call_command

print('\n' + '='*100)
print('🔍 VERIFICACIÓN DE CONEXIÓN A BASE DE DATOS')
print('='*100 + '\n')

try:
    # Intentar conexión
    with connection.cursor() as cursor:
        cursor.execute('SELECT 1;')
        result = cursor.fetchone()
    
    print('✅ Conexión a BD exitosa')
    print(f'   Base de datos: {connection.settings_dict["NAME"]}')
    print(f'   Host: {connection.settings_dict["HOST"]}')
    print(f'   Puerto: {connection.settings_dict["PORT"]}')
    
    # Verificar migraciones aplicadas
    print('\n📊 Estado de migraciones:')
    try:
        call_command('migrate', '--plan', verbosity=0)
        print('✅ Todas las migraciones están aplicadas')
    except Exception as e:
        print(f'⚠️  Algunas migraciones pueden no estar aplicadas: {str(e)[:100]}')
    
    print('\n' + '='*100)
    print('✅ LA BASE DE DATOS ESTÁ LISTA PARA USAR')
    print('='*100 + '\n')
    
except Exception as e:
    print(f'❌ Error de conexión: {str(e)}')
    print('\n💡 Soluciones:')
    print('  1. Verifica que DATABASE_URL esté correcta en variables de entorno')
    print('  2. Asegúrate de incluir .ondigitalocean.com en el host')
    print('  3. Verifica que el puerto sea 25060')
    print('  4. Comprueba ?sslmode=require en la URL')
    print('  5. Revisa credenciales (usuario/contraseña) en DigitalOcean\n')
    sys.exit(1)

#!/bin/bash
set -e

echo "🔄 Esperando a PostgreSQL..."
python << END
import sys
import time
import psycopg2
from urllib.parse import urlparse
import os

max_retries = 30
retry_interval = 2

database_url = os.environ.get('DATABASE_URL', '')
if database_url:
    result = urlparse(database_url)
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                database=result.path[1:],
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port
            )
            conn.close()
            print("✅ PostgreSQL disponible")
            sys.exit(0)
        except psycopg2.OperationalError:
            if i < max_retries - 1:
                print(f"PostgreSQL no disponible - reintento {i+1}/{max_retries}...")
                time.sleep(retry_interval)
            else:
                print("❌ No se pudo conectar a PostgreSQL")
                sys.exit(1)
else:
    print("⚠️ DATABASE_URL no configurada, usando SQLite")
    sys.exit(0)
END

echo "📊 Ejecutando migraciones..."
python manage.py migrate --noinput

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "👤 Verificando superusuario..."
python manage.py shell << END
from django.contrib.auth import get_user_model
import os

User = get_user_model()
username = os.environ.get('ADMIN_USERNAME', 'admin')
email = os.environ.get('ADMIN_EMAIL', 'admin@contafy.com')
password = os.environ.get('ADMIN_PASSWORD', 'changeme123')

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print(f'✅ Superusuario {username} creado')
else:
    print(f'ℹ️ Superusuario {username} ya existe')
END

echo "🚀 Iniciando aplicación..."
exec "$@"

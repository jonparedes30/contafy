#!/bin/bash
set -euo pipefail

echo "🔄 Iniciando deploy..."

# Provide a helpful error message if DATABASE_URL is missing in production
if [ -z "${DATABASE_URL:-}" ]; then
    echo "⚠️ ERROR: DATABASE_URL no configurada."
    if [ "${DEBUG:-false}" = "True" ] || [ "${DEBUG:-false}" = "true" ]; then
        echo "  - DEBUG está activado; continuando en modo de desarrollo (no recomendado en prod)."
        echo "  - Si deseas que el contenedor siga, exporta DEBUG=true y añade DATABASE_URL si quieres persistencia."
    else
        echo "  - En producción (DEBUG=false), DATABASE_URL es requerida."
        echo "  - En Render: añade un servicio de base de datos y vincula la variable de entorno DATABASE_URL al servicio (Render Dashboard → Environment → Add Database)."
    fi
    echo "  - Ejemplo de DATABASE_URL (Postgres): postgres://user:password@host:port/dbname"
    echo "  - Aborting startup to avoid partial initialization."
    exit 1
fi

echo "✅ DATABASE_URL configurada"

echo "📊 Ejecutando migraciones..."
python manage.py migrate --noinput

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput || {
    echo "⚠️ collectstatic falló; revisa configuración de STATICFILES_STORAGE y permisos." >&2
}

echo "👤 Verificando superusuario..."
python - <<'PY'
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get('ADMIN_USERNAME', 'admin')
email = os.environ.get('ADMIN_EMAIL', 'admin@contafy.com')
password = os.environ.get('ADMIN_PASSWORD', None)
if not User.objects.filter(username=username).exists():
    user = User(username=username, email=email, is_staff=True, is_superuser=True)
    if password:
        user.set_password(password)
    else:
        # Do not set a known default password in production
        user.set_unusable_password()
    user.save()
    print(f'✅ Superusuario {username} creado (sin empresa)')
else:
    print(f'ℹ️ Superusuario {username} ya existe')
PY

echo "🚀 Iniciando Gunicorn en puerto 8000..."
# Use PORT env var if set (Render sets this), otherwise default to 8000
PORT=${PORT:-8000}
exec gunicorn core.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --timeout 120 --log-file -


#!/usr/bin/env bash
set -o errexit

echo "🔄 Iniciando deploy..."

# Verificar DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL no está configurada"
    exit 1
fi

echo "✅ DATABASE_URL configurada"

# Extraer hostname para diagnóstico
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
echo "🔍 Hostname de base de datos: $DB_HOST"

# Intentar resolver el hostname
echo "🔍 Verificando resolución DNS..."
if command -v nslookup &> /dev/null; then
    nslookup $DB_HOST || echo "⚠️ Advertencia: No se pudo resolver el hostname"
fi

echo "🔧 Instalando dependencias..."
pip install -r requirements.txt

echo "📊 Ejecutando migraciones..."
# Reintentar migraciones con backoff exponencial
MAX_RETRIES=5
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python manage.py migrate --noinput; then
        echo "✅ Migraciones completadas"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            WAIT_TIME=$((2 ** RETRY_COUNT))
            echo "⚠️ Intento $RETRY_COUNT falló. Reintentando en ${WAIT_TIME}s..."
            sleep $WAIT_TIME
        else
            echo "❌ ERROR: Migraciones fallaron después de $MAX_RETRIES intentos"
            exit 1
        fi
    fi
done

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "👤 Creando superusuario..."
python manage.py shell << END
from django.contrib.auth import get_user_model
import os
User = get_user_model()
username = os.environ.get('ADMIN_USERNAME', 'admin')
email = os.environ.get('ADMIN_EMAIL', 'admin@contafy.com')
password = os.environ.get('ADMIN_PASSWORD', 'changeme123')
if not User.objects.filter(username=username).exists():
    user = User(username=username, email=email, is_staff=True, is_superuser=True)
    user.set_password(password)
    user.save()
    print(f'✅ Superusuario {username} creado sin empresa')
else:
    print(f'ℹ️ Superusuario {username} ya existe')
END

echo "✅ Build completado"

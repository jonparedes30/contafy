#!/usr/bin/env bash
set -o errexit

echo "🔄 Iniciando deploy en Render..."
echo "📅 Fecha: $(date)"
echo "🐍 Python version: $(python --version)"

# Verificar DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERROR: DATABASE_URL no está configurada"
    echo "💡 Configura DATABASE_URL en Render Dashboard → Environment"
    exit 1
fi

echo "✅ DATABASE_URL configurada"

# Extraer hostname para diagnóstico
DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\).*/\1/p')
echo "🔍 Hostname de base de datos: $DB_HOST"

# Verificar conectividad básica
echo "🔍 Verificando conectividad..."
if command -v ping &> /dev/null; then
    ping -c 1 $DB_HOST &> /dev/null && echo "✅ Host alcanzable" || echo "⚠️ Host no responde a ping"
fi

echo "🔧 Instalando dependencias..."
pip install --no-cache-dir -r requirements.txt
echo "✅ Dependencias instaladas"

echo "📊 Verificando conexión a base de datos..."
python manage.py check --database default || {
    echo "❌ ERROR: No se puede conectar a la base de datos"
    echo "💡 Verifica que la base de datos esté en estado 'Available' en Render"
    exit 1
}

echo "📊 Ejecutando migraciones..."
# Reintentar migraciones con backoff exponencial
MAX_RETRIES=3
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if python manage.py migrate --noinput; then
        echo "✅ Migraciones completadas"
        break
    else
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
            WAIT_TIME=$((RETRY_COUNT * 10))
            echo "⚠️ Intento $RETRY_COUNT falló. Reintentando en ${WAIT_TIME}s..."
            sleep $WAIT_TIME
        else
            echo "❌ ERROR: Migraciones fallaron después de $MAX_RETRIES intentos"
            echo "💡 Revisa los logs de la base de datos en Render Dashboard"
            exit 1
        fi
    fi
done

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "👤 Creando superusuario..."
python manage.py shell << 'END'
from django.contrib.auth import get_user_model
import os
try:
    User = get_user_model()
    username = os.environ.get('ADMIN_USERNAME', 'admin')
    email = os.environ.get('ADMIN_EMAIL', 'admin@contafy.com')
    password = os.environ.get('ADMIN_PASSWORD', 'changeme123')
    
    if not User.objects.filter(username=username).exists():
        user = User(username=username, email=email, is_staff=True, is_superuser=True)
        user.set_password(password)
        user.save()
        print(f'✅ Superusuario {username} creado')
    else:
        print(f'ℹ️ Superusuario {username} ya existe')
except Exception as e:
    print(f'⚠️ Error creando superusuario: {e}')
    print('💡 Puedes crear el superusuario manualmente después del deploy')
END

echo "🎉 Build completado exitosamente"
echo "🌐 La aplicación estará disponible en tu dominio de Render"
echo "🔗 Health check: /health/"
echo "🔗 Admin: /admin/"
echo "🔗 App: /app-beta-2024/"

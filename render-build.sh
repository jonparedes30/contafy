#!/usr/bin/env bash
set -o errexit

echo "🔄 Iniciando build para Render..."

pip install -r requirements.txt

echo "📊 Ejecutando migraciones..."
python manage.py migrate --noinput

echo "📦 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput --clear

echo "✅ Build completado"

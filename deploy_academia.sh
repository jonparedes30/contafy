#!/bin/bash
# Script de despliegue automático para Academia CONTAFY

echo "🚀 Desplegando Academia CONTAFY UX Duolingo..."

# 1. Commit y push
echo "📦 Subiendo cambios..."
git add .
git commit -m "restore: complete UX Duolingo functionality with migration"
git push heroku main

# 2. Aplicar migraciones
echo "🔄 Aplicando migraciones..."
heroku run python manage.py migrate

# 3. Cargar contenido demo
echo "📚 Cargando contenido demo..."
heroku run python manage.py crear_contenido_demo

# 4. Verificar funcionamiento
echo "✅ Verificando funcionamiento..."
curl -I https://contafy-pruebas-30fdb804cc25.herokuapp.com/app-beta-2024/aprendizaje/

echo "🎉 Despliegue completado!"
echo "Verifica en: https://contafy-pruebas-30fdb804cc25.herokuapp.com/app-beta-2024/aprendizaje/"
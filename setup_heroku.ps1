# Script de Configuración Automática para Heroku - CONTAFY
# Ejecutar con: .\setup_heroku.ps1

$APP_NAME = "contafy-pruebas"

Write-Host "🚀 Configurando Heroku para $APP_NAME..." -ForegroundColor Green
Write-Host ""

# 1. Generar SECRET_KEY
Write-Host "📝 Generando SECRET_KEY..." -ForegroundColor Yellow
$SECRET_KEY = python -c "import secrets; print(secrets.token_urlsafe(50))"
if ($SECRET_KEY) {
    heroku config:set SECRET_KEY="$SECRET_KEY" --app $APP_NAME
    Write-Host "✅ SECRET_KEY configurada" -ForegroundColor Green
} else {
    Write-Host "❌ Error generando SECRET_KEY" -ForegroundColor Red
    exit 1
}

# 2. Configurar DEBUG
Write-Host ""
Write-Host "🐛 Configurando DEBUG=False..." -ForegroundColor Yellow
heroku config:set DEBUG=False --app $APP_NAME
Write-Host "✅ DEBUG configurado" -ForegroundColor Green

# 3. Configurar ALLOWED_HOSTS
Write-Host ""
Write-Host "🌐 Configurando ALLOWED_HOSTS..." -ForegroundColor Yellow
heroku config:set ALLOWED_HOSTS="contafy-pruebas-30fdb804cc25.herokuapp.com,.herokuapp.com,localhost,127.0.0.1" --app $APP_NAME
Write-Host "✅ ALLOWED_HOSTS configurado" -ForegroundColor Green

# 4. Verificar Postgres
Write-Host ""
Write-Host "🗄️ Verificando Postgres..." -ForegroundColor Yellow
$postgres = heroku addons --app $APP_NAME | Select-String "postgres"
if ($postgres) {
    Write-Host "✅ Postgres ya está provisionado" -ForegroundColor Green
} else {
    Write-Host "⚠️ Provisionando Postgres..." -ForegroundColor Yellow
    heroku addons:create heroku-postgresql:mini --app $APP_NAME
    Write-Host "✅ Postgres provisionado" -ForegroundColor Green
}

# 5. Verificar configuración
Write-Host ""
Write-Host "📋 Configuración actual:" -ForegroundColor Cyan
heroku config --app $APP_NAME

# 6. Ejecutar migraciones
Write-Host ""
Write-Host "📊 Ejecutando migraciones..." -ForegroundColor Yellow
heroku run python manage.py migrate --app $APP_NAME
Write-Host "✅ Migraciones completadas" -ForegroundColor Green

# 7. Recolectar estáticos
Write-Host ""
Write-Host "📦 Recolectando archivos estáticos..." -ForegroundColor Yellow
heroku run python manage.py collectstatic --noinput --app $APP_NAME
Write-Host "✅ Estáticos recolectados" -ForegroundColor Green

# 8. Reiniciar aplicación
Write-Host ""
Write-Host "🔄 Reiniciando aplicación..." -ForegroundColor Yellow
heroku restart --app $APP_NAME
Start-Sleep -Seconds 5
Write-Host "✅ Aplicación reiniciada" -ForegroundColor Green

# 9. Verificar estado
Write-Host ""
Write-Host "✅ Verificando estado..." -ForegroundColor Yellow
heroku ps --app $APP_NAME

# 10. Abrir aplicación
Write-Host ""
Write-Host "🌐 Abriendo aplicación en navegador..." -ForegroundColor Yellow
heroku open --app $APP_NAME

# 11. Mostrar logs
Write-Host ""
Write-Host "📋 Mostrando logs (Ctrl+C para salir)..." -ForegroundColor Cyan
Write-Host ""
heroku logs --tail --app $APP_NAME

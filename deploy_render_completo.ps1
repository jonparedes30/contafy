# Script de Deploy Completo para Render - CONTAFY Academia
# Ejecutar: .\deploy_render_completo.ps1

Write-Host "🚀 DEPLOY A RENDER - CONTAFY ACADEMIA" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar Git
Write-Host "📋 Verificando estado de Git..." -ForegroundColor Yellow
$gitStatus = git status --porcelain

if ($gitStatus) {
    Write-Host "⚠️  Hay cambios sin commitear:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    
    $commit = Read-Host "¿Deseas commitear estos cambios? (s/n)"
    
    if ($commit -eq "s" -or $commit -eq "S") {
        $mensaje = Read-Host "Mensaje del commit"
        if (-not $mensaje) {
            $mensaje = "feat: actualización para deploy en Render"
        }
        
        Write-Host "📝 Commiteando cambios..." -ForegroundColor Yellow
        git add .
        git commit -m $mensaje
        
        Write-Host "✅ Cambios commiteados" -ForegroundColor Green
    } else {
        Write-Host "❌ Deploy cancelado. Commitea los cambios primero." -ForegroundColor Red
        exit 1
    }
}

# 2. Verificar rama actual
$rama = git branch --show-current
Write-Host "📍 Rama actual: $rama" -ForegroundColor Cyan

# 3. Push a GitHub
Write-Host ""
Write-Host "📤 Pusheando a GitHub..." -ForegroundColor Yellow
git push origin $rama

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Push exitoso" -ForegroundColor Green
} else {
    Write-Host "❌ Error en push. Verifica tu conexión y permisos." -ForegroundColor Red
    exit 1
}

# 4. Información de deploy
Write-Host ""
Write-Host "✅ CÓDIGO LISTO PARA DEPLOY" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""
Write-Host "📋 PRÓXIMOS PASOS EN RENDER:" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Ve a: https://dashboard.render.com" -ForegroundColor White
Write-Host ""
Write-Host "2. Si es tu primer deploy:" -ForegroundColor Yellow
Write-Host "   - New + → PostgreSQL" -ForegroundColor White
Write-Host "     • Name: contafy-db" -ForegroundColor Gray
Write-Host "     • Plan: Starter" -ForegroundColor Gray
Write-Host "   - New + → Web Service" -ForegroundColor White
Write-Host "     • Connect tu repo: contafy" -ForegroundColor Gray
Write-Host "     • Environment: Docker" -ForegroundColor Gray
Write-Host "     • Plan: Starter" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Configurar Variables de Entorno:" -ForegroundColor Yellow
Write-Host "   SECRET_KEY: [Generate]" -ForegroundColor Gray
Write-Host "   DEBUG: False" -ForegroundColor Gray
Write-Host "   DJANGO_SETTINGS_MODULE: core.settings" -ForegroundColor Gray
Write-Host "   DATABASE_URL: [From PostgreSQL]" -ForegroundColor Gray
Write-Host "   ALLOWED_HOSTS: .onrender.com,localhost,127.0.0.1" -ForegroundColor Gray
Write-Host "   RENDER: true" -ForegroundColor Gray
Write-Host "   ADMIN_USERNAME: admin" -ForegroundColor Gray
Write-Host "   ADMIN_EMAIL: admin@contafy.com" -ForegroundColor Gray
Write-Host "   ADMIN_PASSWORD: [Tu contraseña segura]" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Click 'Create Web Service' y esperar 5-10 minutos" -ForegroundColor Yellow
Write-Host ""
Write-Host "5. Verificar deploy:" -ForegroundColor Yellow
Write-Host "   https://contafy.onrender.com/health/" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentación completa: MIGRACION_RENDER_COMPLETA.md" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎉 ¡Listo para producción!" -ForegroundColor Green
Write-Host ""

# Preguntar si desea abrir el dashboard
$abrir = Read-Host "¿Abrir Render Dashboard en el navegador? (s/n)"
if ($abrir -eq "s" -or $abrir -eq "S") {
    Start-Process "https://dashboard.render.com"
}

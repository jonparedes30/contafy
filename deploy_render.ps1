# Script de Deploy a Render - CONTAFY
# Ejecutar con: .\deploy_render.ps1

Write-Host "🚀 Preparando deploy a Render..." -ForegroundColor Green
Write-Host ""

# 1. Verificar rama actual
$BRANCH = git branch --show-current
Write-Host "📍 Rama actual: $BRANCH" -ForegroundColor Cyan

# 2. Verificar cambios sin commit
$STATUS = git status --porcelain
if ($STATUS) {
    Write-Host "⚠️ Hay cambios sin commit:" -ForegroundColor Yellow
    git status --short
    Write-Host ""
    $response = Read-Host "¿Deseas commitear estos cambios? (s/n)"
    if ($response -eq 's') {
        $message = Read-Host "Mensaje del commit"
        git add .
        git commit -m "$message"
        Write-Host "✅ Cambios commiteados" -ForegroundColor Green
    } else {
        Write-Host "❌ Deploy cancelado" -ForegroundColor Red
        exit 1
    }
}

# 3. Push a GitHub
Write-Host ""
Write-Host "📤 Pushing a GitHub..." -ForegroundColor Yellow
git push origin $BRANCH

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Push exitoso" -ForegroundColor Green
} else {
    Write-Host "❌ Error en push" -ForegroundColor Red
    exit 1
}

# 4. Información
Write-Host ""
Write-Host "✅ Deploy iniciado en Render" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Próximos pasos:" -ForegroundColor Cyan
Write-Host "1. Ve a https://dashboard.render.com" -ForegroundColor White
Write-Host "2. Verifica que el deploy esté en progreso" -ForegroundColor White
Write-Host "3. Espera 5-10 minutos para que complete" -ForegroundColor White
Write-Host "4. Prueba tu app en: https://contafy.onrender.com/health/" -ForegroundColor White
Write-Host ""
Write-Host "🌐 URLs importantes:" -ForegroundColor Cyan
Write-Host "   Health: https://contafy.onrender.com/health/" -ForegroundColor White
Write-Host "   Login:  https://contafy.onrender.com/app-beta-2024/login/" -ForegroundColor White
Write-Host "   Admin:  https://contafy.onrender.com/admin/" -ForegroundColor White
Write-Host ""

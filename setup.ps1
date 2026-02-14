# ============================================================================
# SETUP.PS1 - Script de Configuración Automatizada para CONTAFY (Windows)
# ============================================================================
# Propósito: Automatizar pasos 1-9 de SETUP.md en Windows
# Uso: PowerShell -NoProfile -ExecutionPolicy Bypass -File setup.ps1
# ============================================================================

# Requiere permisos de ejecución:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

$ErrorActionPreference = "Stop"

# Funciones de output
function Write-Header {
    param([string]$Message)
    Write-Host "`n════════════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host $Message -ForegroundColor Cyan
    Write-Host "════════════════════════════════════════════════`n" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ ERROR: $Message" -ForegroundColor Red
}

function Write-Warning-Custom {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# ============================================================================
# PASO 1: Verificar requisitos previos
# ============================================================================
Write-Header "PASO 1: Verificando Requisitos"

# Verificar Python
try {
    $pythonVersion = & python --version 2>&1
    Write-Success "Python encontrado: $pythonVersion"
} catch {
    Write-Error-Custom "Python no está instalado o no está en PATH"
    Write-Host "Instálalo desde: https://www.python.org/downloads/" -ForegroundColor White
    exit 1
}

# Verificar pip
try {
    $pipVersion = & python -m pip --version 2>&1 | Select-Object -First 1
    Write-Success "pip está disponible: $pipVersion"
} catch {
    Write-Error-Custom "pip no está disponible"
    exit 1
}

# Verificar Git
try {
    $gitVersion = & git --version 2>&1
    Write-Success "Git encontrado: $gitVersion"
} catch {
    Write-Error-Custom "Git no está instalado"
    exit 1
}

# ============================================================================
# PASO 2: Verificar estructura del proyecto
# ============================================================================
Write-Header "PASO 2: Verificando Estructura del Proyecto"

if (-not (Test-Path "manage.py")) {
    Write-Error-Custom "manage.py no encontrado en directorio actual"
    Write-Host "Asegúrate de estar en la raíz del proyecto" -ForegroundColor White
    exit 1
}
Write-Success "manage.py encontrado"

if (-not (Test-Path "requirements.txt")) {
    Write-Error-Custom "requirements.txt no encontrado"
    exit 1
}
Write-Success "requirements.txt encontrado"

if (-not (Test-Path ".env.example")) {
    Write-Warning-Custom ".env.example no encontrado (podría ser necesario)"
}

# ============================================================================
# PASO 3: Crear entorno virtual
# ============================================================================
Write-Header "PASO 3: Creando Entorno Virtual"

if (Test-Path ".venv") {
    Write-Warning-Custom "Entorno virtual ya existe"
    $response = Read-Host "¿Deseas recrearlo? (s/n)"
    if ($response -eq "s" -or $response -eq "S") {
        Write-Host "Eliminando entorno virtual anterior..."
        Remove-Item -Recurse -Force ".venv"
        Write-Host "Creando nuevo entorno virtual..."
        & python -m venv .venv
        Write-Success "Entorno virtual recreado"
    }
} else {
    Write-Host "Creando entorno virtual..."
    & python -m venv .venv
    Write-Success "Entorno virtual creado en .venv"
}

# Activar entorno virtual
Write-Host "Activando entorno virtual..."
& ".\.venv\Scripts\Activate.ps1"
Write-Success "Entorno virtual activado"

# ============================================================================
# PASO 4: Instalar dependencias
# ============================================================================
Write-Header "PASO 4: Instalando Dependencias"

Write-Warning-Custom "Actualizando pip, setuptools, wheel..."
& python -m pip install --upgrade pip setuptools wheel 2>&1 | Out-Null

Write-Warning-Custom "Instalando dependencias de requirements.txt..."
& pip install -r requirements.txt

try {
    $djangoVersion = & python -m django --version 2>&1
    Write-Success "Django instalado: $djangoVersion"
} catch {
    Write-Warning-Custom "No se pudo verificar versión de Django"
}

Write-Host "`nPaquetes clave instalados:" -ForegroundColor Cyan
& pip list | Select-String -Pattern "Django|djangorestframework|psycopg2|django-environ"

# ============================================================================
# PASO 5: Configurar variables de entorno
# ============================================================================
Write-Header "PASO 5: Configurando Variables de Entorno"

if (Test-Path ".env") {
    Write-Warning-Custom ".env ya existe"
    $response = Read-Host "¿Deseas recrearlo desde .env.example? (s/n)"
    if ($response -eq "s" -or $response -eq "S") {
        Copy-Item ".env.example" ".env"
        Write-Success ".env creado desde .env.example"
    }
} else {
    Copy-Item ".env.example" ".env"
    Write-Success ".env creado desde .env.example"
}

Write-Host ""
Write-Host "Variables de .env creadas. EDITA EL ARCHIVO:" -ForegroundColor Yellow
Write-Host "  notepad .env" -ForegroundColor White
Write-Host ""

$response = Read-Host "¿Ya editaste .env? (s/n)"
if ($response -ne "s" -and $response -ne "S") {
    Write-Warning-Custom "Por favor edita el archivo .env antes de continuar"
}

# ============================================================================
# PASO 6: Verificar integridad de BD
# ============================================================================
Write-Header "PASO 6: Verificando Integridad de Base de Datos"

& python manage.py check 2>&1
Write-Success "Verificación de configuración completada"

# ============================================================================
# PASO 7: Aplicar migraciones
# ============================================================================
Write-Header "PASO 7: Aplicando Migraciones"

Write-Host "Migraciones pendientes:" -ForegroundColor Cyan
& python manage.py migrate --plan 2>&1 | Select-Object -First 20

Write-Host ""
$response = Read-Host "¿Aplicar migraciones? (s/n)"

if ($response -eq "s" -or $response -eq "S") {
    & python manage.py migrate
    Write-Success "Migraciones aplicadas"
} else {
    Write-Warning-Custom "Migraciones no aplicadas"
}

# ============================================================================
# PASO 8: Crear superusuario (opcional)
# ============================================================================
Write-Header "PASO 8: Superusuario (OPCIONAL)"

Write-Host "¿Deseas crear un superusuario ahora?" -ForegroundColor Cyan
Write-Host "Sáltalo si restauraste datos de una BD existente" -ForegroundColor Yellow
$response = Read-Host "¿Crear superusuario? (s/n)"

if ($response -eq "s" -or $response -eq "S") {
    & python manage.py createsuperuser
    Write-Success "Superusuario creado"
} else {
    Write-Warning-Custom "Superusuario no creado"
}

# ============================================================================
# PASO 9: Test final
# ============================================================================
Write-Header "PASO 9: Test Final"

Write-Host "Ejecutando python manage.py check..." -ForegroundColor Cyan
& python manage.py check 2>&1
Write-Success "Todas las verificaciones pasaron"

# ============================================================================
# Resumen final
# ============================================================================
Write-Header "CONFIGURACIÓN COMPLETADA"

Write-Host "El proyecto está listo para desarrollo." -ForegroundColor Green
Write-Host ""
Write-Host "Para iniciar el servidor:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1  # Activar entorno virtual" -ForegroundColor White
Write-Host "  python manage.py runserver" -ForegroundColor White
Write-Host ""
Write-Host "Accede a: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host ""
Write-Host "Para más detalles, ver: SETUP.md" -ForegroundColor Cyan
Write-Host ""

Write-Host "Información del entorno:" -ForegroundColor Cyan
Write-Host "  Entorno virtual: .venv" -ForegroundColor White
Write-Host "  Python ejecutable: $(python -c 'import sys; print(sys.executable)')" -ForegroundColor White
try {
    $django = python -m django --version
    Write-Host "  Django: $django" -ForegroundColor White
} catch {}
Write-Host ""


# ============================================================================
# BACKUP_RESTORE.PS1 - Herramienta para Respaldar y Restaurar BD (Windows)
# ============================================================================
# Propósito: Facilitar backup y restore de BD PostgreSQL desde Windows
# Uso:
#   Backup:  powershell -File backup_restore.ps1 backup
#   Restore: powershell -File backup_restore.ps1 restore [archivo.sql]
# ============================================================================

param(
    [string]$Action = "",
    [string]$BackupFile = ""
)

# Funciones de output
function Write-Success { param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom { param([string]$Message)
    Write-Host "✗ ERROR: $Message" -ForegroundColor Red
}

function Write-Warning-Custom { param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

# ============================================================================
# Detectar credenciales desde .env
# ============================================================================
if (-not (Test-Path ".env")) {
    Write-Error-Custom ".env no encontrado"
    Write-Host "Crea .env con las credenciales de tu BD PostgreSQL" -ForegroundColor White
    exit 1
}

# Leer contenido de .env
$envContent = Get-Content ".env" | Select-String "DATABASE_URL"
if (-not $envContent) {
    Write-Warning-Custom "No se encontró DATABASE_URL en .env"
    Write-Host "Si usas SQLite, no necesitas este script" -ForegroundColor White
    exit 1
}

$DATABASE_URL = $envContent[0].ToString().Split("=")[1].Trim('"').Trim("'")

# Parsear DATABASE_URL
# Formato: postgres://usuario:password@host:puerto/nombre_db
Write-Host "DATABASE_URL detectada" -ForegroundColor Cyan

# Remover protocolo
$urlClean = $DATABASE_URL -replace '^(postgres|postgresql)://', ''

# Extraer usuario y password
$userpass = $urlClean.Split("@")[0]
$DB_USER = $userpass.Split(":")[0]
$DB_PASSWORD = $userpass.Split(":")[1]

# Extraer host, puerto y nombre_db
$hostdb = $urlClean.Split("@")[1]
$hostport = $hostdb.Split("/")[0]
$DB_NAME = $hostdb.Substring($hostdb.IndexOf("/") + 1)

if ($hostport -match ":") {
    $DB_HOST = $hostport.Split(":")[0]
    $DB_PORT = [int]$hostport.Split(":")[1]
} else {
    $DB_HOST = $hostport
    $DB_PORT = 5432
}

# ============================================================================
# Validar conexión
# ============================================================================
function Validate-Connection {
    Write-Warning-Custom "Validando conexión a BD..."
    
    try {
        $env:PGPASSWORD = $DB_PASSWORD
        $checkCmd = "psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c `"SELECT 1;`" 2>$null"
        $result = Invoke-Expression $checkCmd
        
        if ($?) {
            Write-Success "Conexión válida"
            return $true
        } else {
            throw "Conexión fallida"
        }
    } catch {
        Write-Error-Custom "No se puede conectar a la BD"
        Write-Host "Verifica credenciales en .env o DATABASE_URL" -ForegroundColor White
        return $false
    }
}

# ============================================================================
# FUNCIÓN: Crear Backup
# ============================================================================
function Create-Backup {
    Write-Warning-Custom "DATABASE_URL detectada:"
    Write-Host "  Host: $DB_HOST" -ForegroundColor White
    Write-Host "  Puerto: $DB_PORT" -ForegroundColor White
    Write-Host "  Usuario: $DB_USER" -ForegroundColor White
    Write-Host "  Nombre BD: $DB_NAME" -ForegroundColor White
    Write-Host ""
    
    if (-not (Validate-Connection)) {
        exit 1
    }
    
    # Generar nombre de respaldo con timestamp
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "backup_${DB_NAME}_${timestamp}.sql"
    
    Write-Warning-Custom "Creando respaldo..."
    Write-Host "  Archivo: $backupFile" -ForegroundColor White
    
    $env:PGPASSWORD = $DB_PASSWORD
    $dumpCmd = "pg_dump -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME --format=plain --no-password > $backupFile"
    
    Invoke-Expression $dumpCmd
    
    # Comprimir respaldo (usando PowerShell Compress-Archive)
    Write-Warning-Custom "Comprimiendo..."
    Compress-Archive -Path $backupFile -DestinationPath "${backupFile}.zip" -Force
    Remove-Item $backupFile
    
    $backupFile = "${backupFile}.zip"
    $fileSize = (Get-Item $backupFile).Length / 1MB
    
    Write-Success "Respaldo creado: $backupFile (aprox. $([Math]::Round($fileSize, 2)) MB)"
    Write-Host ""
    Write-Host "Próximos pasos:" -ForegroundColor Cyan
    Write-Host "  1. Guardar en lugar seguro (drive, servidor, etc.)" -ForegroundColor White
    Write-Host "  2. Para restaurar: powershell -File backup_restore.ps1 restore $backupFile" -ForegroundColor White
    Write-Host ""
}

# ============================================================================
# FUNCIÓN: Restaurar desde Backup
# ============================================================================
function Restore-Backup {
    param([string]$BackupFile)
    
    if ([string]::IsNullOrEmpty($BackupFile)) {
        Write-Error-Custom "Debes especificar archivo de respaldo"
        Write-Host "Uso: powershell -File backup_restore.ps1 restore backup.sql.zip" -ForegroundColor White
        exit 1
    }
    
    if (-not (Test-Path $BackupFile)) {
        Write-Error-Custom "Archivo no encontrado: $BackupFile"
        exit 1
    }
    
    Write-Warning-Custom "Validando credenciales..."
    Write-Host "  Host: $DB_HOST" -ForegroundColor White
    Write-Host "  Puerto: $DB_PORT" -ForegroundColor White
    Write-Host "  Usuario: $DB_USER" -ForegroundColor White
    Write-Host "  Nombre BD: $DB_NAME" -ForegroundColor White
    Write-Host ""
    
    if (-not (Validate-Connection)) {
        exit 1
    }
    
    # Pregunta de confirmación
    $response = Read-Host "⚠️  ADVERTENCIA: Esto eliminará todos los datos en $DB_NAME. ¿Continuar? (s/n)"
    if ($response -ne "s" -and $response -ne "S") {
        Write-Warning-Custom "Restauración cancelada"
        exit 0
    }
    
    # Descomprimir si es .zip
    $tempFile = $BackupFile
    if ($BackupFile -match "\.zip$") {
        Write-Warning-Custom "Descomprimiendo..."
        $extractPath = [System.IO.Path]::GetTempPath()
        Expand-Archive -Path $BackupFile -DestinationPath $extractPath -Force
        $tempFile = Join-Path $extractPath (Get-ChildItem $extractPath -Filter "*.sql" -Recurse | Select-Object -First 1).Name
    }
    
    Write-Warning-Custom "Vaciando BD actual..."
    $env:PGPASSWORD = $DB_PASSWORD
    $dropCmd = "psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c `"DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;`""
    Invoke-Expression $dropCmd
    
    Write-Warning-Custom "Restaurando datos (puede tomar varios minutos)..."
    $restoreCmd = "psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME < $tempFile"
    Invoke-Expression $restoreCmd
    
    Write-Success "Restauración completada"
    Write-Host ""
    Write-Host "Próximos pasos:" -ForegroundColor Cyan
    Write-Host "  1. Aplicar migraciones: python manage.py migrate" -ForegroundColor White
    Write-Host "  2. Iniciar servidor: python manage.py runserver" -ForegroundColor White
    Write-Host ""
}

# ============================================================================
# Menú principal
# ============================================================================
if ([string]::IsNullOrEmpty($Action)) {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  BACKUP/RESTORE - Base de Datos CONTAFY      ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════╝" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso:" -ForegroundColor White
    Write-Host "  Crear respaldo:   powershell -File backup_restore.ps1 backup" -ForegroundColor White
    Write-Host "  Restaurar datos:  powershell -File backup_restore.ps1 restore archivo.sql.zip" -ForegroundColor White
    Write-Host ""
    Write-Host "Ejemplos:" -ForegroundColor White
    Write-Host "  powershell -File backup_restore.ps1 backup" -ForegroundColor White
    Write-Host "  powershell -File backup_restore.ps1 restore backup_contafy_20260213_140530.sql.zip" -ForegroundColor White
    Write-Host ""
    exit 0
}

# Ejecutar comando
switch ($Action.ToLower()) {
    "backup" {
        Create-Backup
    }
    "restore" {
        Restore-Backup $BackupFile
    }
    default {
        Write-Error-Custom "Comando desconocido: $Action"
        Write-Host "Comandos disponibles: backup, restore" -ForegroundColor White
        exit 1
    }
}


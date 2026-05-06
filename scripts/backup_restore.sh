#!/bin/bash
# ============================================================================
# BACKUP_RESTORE.SH - Herramienta para Respaldar y Restaurar Base de Datos
# ============================================================================
# Propósito: Facilitar backup y restore de BD PostgreSQL
# Uso:
#   Backup:  bash backup_restore.sh backup
#   Restore: bash backup_restore.sh restore [archivo.sql]
# ============================================================================

set -e

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_warning() { echo -e "${YELLOW}⚠ $1${NC}"; }

# ============================================================================
# Detectar credenciales desde .env
# ============================================================================
if [ ! -f ".env" ]; then
    print_error ".env no encontrado"
    echo "Crea .env con las credenciales de tu BD PostgreSQL"
    exit 1
fi

# Extraer valores de .env
extract_db_value() {
    local key=$1
    grep "^${key}=" .env | cut -d'=' -f2- | tr -d '"' | tr -d "'"
}

# Intentar extraer DATABASE_URL
DATABASE_URL=$(extract_db_value "DATABASE_URL" || echo "")

if [ -z "$DATABASE_URL" ]; then
    print_warning "No se encontró DATABASE_URL en .env"
    echo "Si usas SQLite, no necesitas este script"
    exit 1
fi

# Parsear DATABASE_URL
# Formato: postgres://usuario:password@host:puerto/nombre_db
parse_db_url() {
    local url=$1
    # Remover protocolo
    url=${url#postgres://}
    url=${url#postgresql://}
    
    # Extraer usuario y password
    local userpass=${url%@*}
    DB_USER=${userpass%:*}
    DB_PASSWORD=${userpass#*:}
    
    # Extraer host, puerto y nombre_db
    local hostdb=${url#*@}
    local host_port=${hostdb%/*}
    DB_NAME=${hostdb#*/}
    
    if [[ $host_port == *:* ]]; then
        DB_HOST=${host_port%:*}
        DB_PORT=${host_port#*:}
    else
        DB_HOST=$host_port
        DB_PORT=5432
    fi
}

parse_db_url "$DATABASE_URL"

# ============================================================================
# Validar conexión
# ============================================================================
validate_connection() {
    print_warning "Validando conexión a BD..."
    
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" > /dev/null 2>&1; then
        print_success "Conexión válida"
        return 0
    else
        print_error "No se puede conectar a la BD"
        echo "Verifica credenciales en .env o DATABASE_URL"
        return 1
    fi
}

# ============================================================================
# FUNCIÓN: Crear Backup
# ============================================================================
create_backup() {
    print_warning "DATABASE_URL detectada:"
    echo "  Host: $DB_HOST"
    echo "  Puerto: $DB_PORT"
    echo "  Usuario: $DB_USER"
    echo "  Nombre BD: $DB_NAME"
    echo ""
    
    if ! validate_connection; then
        exit 1
    fi
    
    # Generar nombre de respaldo con timestamp
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="backup_${DB_NAME}_${TIMESTAMP}.sql"
    
    print_warning "Creando respaldo..."
    echo "  Archivo: $BACKUP_FILE"
    
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --format=plain \
        --no-password \
        > "$BACKUP_FILE"
    
    # Comprimir respaldo
    gzip "$BACKUP_FILE"
    BACKUP_FILE="${BACKUP_FILE}.gz"
    
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    print_success "Respaldo creado: $BACKUP_FILE ($FILE_SIZE)"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Guardar en lugar seguro (drive, servidor, etc.)"
    echo "  2. Para restaurar: bash backup_restore.sh restore $BACKUP_FILE"
    echo ""
}

# ============================================================================
# FUNCIÓN: Restaurar desde Backup
# ============================================================================
restore_backup() {
    local backup_file=$1
    
    if [ -z "$backup_file" ]; then
        print_error "Debes especificar archivo de respaldo"
        echo "Uso: bash backup_restore.sh restore backup.sql.gz"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Archivo no encontrado: $backup_file"
        exit 1
    fi
    
    print_warning "Validando credenciales..."
    echo "  Host: $DB_HOST"
    echo "  Puerto: $DB_PORT"
    echo "  Usuario: $DB_USER"
    echo "  Nombre BD: $DB_NAME"
    echo ""
    
    if ! validate_connection; then
        exit 1
    fi
    
    # Preguntar confirmación
    echo "⚠️  ADVERTENCIA: Esto eliminará todos los datos actuales en $DB_NAME"
    read -p "¿Continuar? (s/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        print_warning "Restauración cancelada"
        exit 0
    fi
    
    # Descomprimir si es .gz
    local temp_file="$backup_file"
    if [[ "$backup_file" == *.gz ]]; then
        print_warning "Descomprimiendo..."
        temp_file="${backup_file%.gz}"
        gunzip -c "$backup_file" > "$temp_file"
    fi
    
    print_warning "Vaciando BD actual..."
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"
    
    print_warning "Restaurando datos (puede tomar varios minutos)..."
    PGPASSWORD="$DB_PASSWORD" psql \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        < "$temp_file"
    
    # Limpiar archivo temporal si se descomprimió
    if [[ "$backup_file" == *.gz ]]; then
        rm "$temp_file"
    fi
    
    print_success "Restauración completada"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Aplicar migraciones: python manage.py migrate"
    echo "  2. Iniciar servidor: python manage.py runserver"
    echo ""
}

# ============================================================================
# Menú principal
# ============================================================================
if [ $# -eq 0 ]; then
    echo ""
    echo "╔═══════════════════════════════════════════════╗"
    echo "║  BACKUP/RESTORE - Base de Datos CONTAFY      ║"
    echo "╚═══════════════════════════════════════════════╝"
    echo ""
    echo "Uso:"
    echo "  Crear respaldo:   bash backup_restore.sh backup"
    echo "  Restaurar datos:  bash backup_restore.sh restore archivo.sql.gz"
    echo ""
    echo "Ejemplos:"
    echo "  bash backup_restore.sh backup"
    echo "  bash backup_restore.sh restore backup_contafy_20260213_140530.sql.gz"
    echo ""
    exit 0
fi

# Ejecutar comando
case "$1" in
    backup)
        create_backup
        ;;
    restore)
        restore_backup "$2"
        ;;
    *)
        print_error "Comando desconocido: $1"
        echo "Comandos disponibles: backup, restore"
        exit 1
        ;;
esac


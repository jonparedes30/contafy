#!/bin/bash
# ============================================================================
# SETUP.SH - Script de Configuración Automatizada para CONTAFY
# ============================================================================
# Propósito: Automatizar pasos 1-9 de SETUP.md en Linux/macOS
# Uso: bash setup.sh
# ============================================================================

set -e  # Detener si hay cualquier error

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de output
print_header() {
    echo -e "\n${BLUE}════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# ============================================================================
# PASO 1: Verificar requisitos previos
# ============================================================================
print_header "PASO 1: Verificando Requisitos"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    print_error "Python3 no está instalado"
    echo "Instálalo desde: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_success "Python encontrado: $PYTHON_VERSION"

# Verificar pip
if ! python3 -m pip --version &> /dev/null; then
    print_error "pip no está disponible"
    exit 1
fi
print_success "pip está disponible"

# Verificar Git
if ! command -v git &> /dev/null; then
    print_error "Git no está instalado"
    exit 1
fi
print_success "Git está disponible"

# ============================================================================
# PASO 2: Verificar estructura del proyecto
# ============================================================================
print_header "PASO 2: Verificando Estructura del Proyecto"

if [ ! -f "manage.py" ]; then
    print_error "manage.py no encontrado en directorio actual"
    echo "Asegúrate de estar en la raíz del proyecto"
    exit 1
fi
print_success "manage.py encontrado"

if [ ! -f "requirements.txt" ]; then
    print_error "requirements.txt no encontrado"
    exit 1
fi
print_success "requirements.txt encontrado"

if [ ! -f ".env.example" ]; then
    print_warning ".env.example no encontrado (podría ser necesario)"
fi

# ============================================================================
# PASO 3: Crear entorno virtual
# ============================================================================
print_header "PASO 3: Creando Entorno Virtual"

if [ -d ".venv" ]; then
    print_warning "Entorno virtual ya existe"
    read -p "¿Deseas recrearlo? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
        print_success "Entorno virtual recreado"
    fi
else
    python3 -m venv .venv
    print_success "Entorno virtual creado en .venv"
fi

# Activar entorno virtual
source .venv/bin/activate
print_success "Entorno virtual activado"

# ============================================================================
# PASO 4: Instalar dependencias
# ============================================================================
print_header "PASO 4: Instalando Dependencias"

print_warning "Actualizando pip, setuptools, wheel..."
pip install --upgrade pip setuptools wheel > /dev/null

print_warning "Instalando dependencias de requirements.txt..."
pip install -r requirements.txt

DJANGO_VERSION=$(python3 -m django --version 2>&1)
print_success "Django instalado: $DJANGO_VERSION"

# Listar paquetes instalados
echo ""
echo "Paquetes instalados:"
pip list | grep -E "Django|djangorestframework|psycopg2|django-environ" || true

# ============================================================================
# PASO 5: Configurar variables de entorno
# ============================================================================
print_header "PASO 5: Configurando Variables de Entorno"

if [ -f ".env" ]; then
    print_warning ".env ya existe"
    read -p "¿Deseas recrearlo desde .env.example? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cp .env.example .env
        print_success ".env creado desde .env.example"
    fi
else
    cp .env.example .env
    print_success ".env creado desde .env.example"
fi

echo ""
echo "Variables de .env creadas. EDITA EL ARCHIVO:"
echo "  nano .env"
echo ""
read -p "¿Ya editaste .env? (y/n): " -n 1 -r
echo

# ============================================================================
# PASO 6: Verificar integridad de BD
# ============================================================================
print_header "PASO 6: Verificando Integridad de Base de Datos"

python3 manage.py check
print_success "Verificación de configuración completada"

# ============================================================================
# PASO 7: Aplicar migraciones
# ============================================================================
print_header "PASO 7: Aplicando Migraciones"

echo "Migraciones pendientes:"
python3 manage.py migrate --plan | head -20 || echo "No hay migraciones pendientes"

echo ""
read -p "¿Aplicar migraciones? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 manage.py migrate
    print_success "Migraciones aplicadas"
else
    print_warning "Migraciones no aplicadas"
fi

# ============================================================================
# PASO 8: Crear superusuario (opcional)
# ============================================================================
print_header "PASO 8: Superusuario (OPCIONAL)"

echo "¿Deseas crear un superusuario ahora?"
echo "Sáltalo si restauraste datos de una BD existente"
read -p "¿Crear superusuario? (y/n): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 manage.py createsuperuser
    print_success "Superusuario creado"
else
    print_warning "Superusuario no creado"
fi

# ============================================================================
# PASO 9: Test final
# ============================================================================
print_header "PASO 9: Test Final"

echo "Ejecutando python manage.py check..."
python3 manage.py check
print_success "Todas las verificaciones pasaron"

# ============================================================================
# Resumen final
# ============================================================================
print_header "CONFIGURACIÓN COMPLETADA"

echo "El proyecto está listo para desarrollo."
echo ""
echo "Para iniciar el servidor:"
echo "  source .venv/bin/activate  # Activar entorno virtual"
echo "  python3 manage.py runserver"
echo ""
echo "Accede a: http://127.0.0.1:8000"
echo ""
echo "Para más detalles, ver: SETUP.md"
echo ""

# Mostrar .venv info
echo "Entorno virtual: .venv"
echo "Python ejecutable: $(which python3)"
echo "Django: $DJANGO_VERSION"
echo ""


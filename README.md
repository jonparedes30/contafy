# CONTAFY

Plataforma SaaS de gestión contable-financiera para pymes ecuatorianas.

## Características principales
- Gestión de gastos, ingresos y cuentas contables
- Reportes: balance general, estado de resultados, flujo de caja
- Autenticación JWT segura
- Soporte para PostgreSQL y SQLite (desarrollo)
- Dashboard interactivo con gráficos
- Sistema de demos empresariales

## Requisitos del sistema
- **Python**: 3.11.4+ (mínimo 3.11)
- **Django**: 5.2.3
- **Base de datos**: SQLite (desarrollo) o PostgreSQL (producción)
- **Sistema**: Windows, Linux, o macOS

## ⚡ Instalación Rápida

**⚠️ IMPORTANTE**: Lee el archivo **[SETUP.md](SETUP.md)** para instrucciones paso a paso.

Para una instalación rápida:

```bash
# 1. Clonar el repositorio
git clone https://github.com/tuusuario/contafy.git
cd contafy

# 2. Crear entorno virtual
python -m venv .venv

# 3. Activar entorno virtual
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 4. Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 5. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores (ver abajo)

# 6. Aplicar migraciones
python manage.py migrate

# 7. Ejecutar servidor
python manage.py runserver
# Accede a http://127.0.0.1:8000
```

→ **Para instrucciones detalladas**, ver [SETUP.md](SETUP.md)

## Configuración de Variables de Entorno

Copia el archivo `.env.example` a `.env` y configura tus valores locales:

```bash
cp .env.example .env
# Editar con: nano .env (Linux/Mac) o notepad .env (Windows)
```

### Archivo `.env.example` - Plantilla

```dotenv
# DJANGO
DEBUG=True
SECRET_KEY=tu-clave-secreta-muy-segura-minimo-32-caracteres
ALLOWED_HOSTS=localhost,127.0.0.1

# BASE DE DATOS (elige una opción)
# Opción A: SQLite (desarrollo simple)
# DATABASE_URL=  # Dejar vacío para usar SQLite

# Opción B: PostgreSQL (producción/desarrollo avanzado)
# DATABASE_URL=postgres://usuario:password@localhost:5432/contafy_db

# EMAIL (opcional)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu_email@gmail.com
EMAIL_HOST_PASSWORD=tu_app_password

# WHATSAPP TWILIO (opcional)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=

# LOGS
LOG_LEVEL=INFO

# BACKUPS
BACKUP_ENABLED=True
BACKUP_RETENTION_DAYS=30
```

### Notas Importantes
- ✅ `.env` **NO** se sube a Git (está en `.gitignore`)
- ✅ Cada máquina necesita su propio `.env`
- ✅ Para SQLite: no configures `DATABASE_URL` (dejarlo vacío)
- ✅ Para PostgreSQL: instala `psycopg2-binary` (ya en requirements.txt)
- ⚠️ **Nunca** pongas credenciales reales en código, **siempre** en `.env`

## Restaurar Base de Datos

### Desde respaldo PostgreSQL (si tienes backup.sql)

```bash
# 1. Crear base de datos nueva (si no existe)
createdb -U postgres contafy_db

# 2. Restaurar respaldo
psql -U usuario -d contafy_db < backup.sql

# 3. Actualizar DATABASE_URL en .env
DATABASE_URL=postgres://usuario:password@localhost:5432/contafy_db

# 4. Verificar migraciones
python manage.py migrate --check
```

### Desde respaldo SQLite

```bash
# 1. Copiar archivo de base de datos
cp backup_sqlite.db contafy_sistema.db

# 2. Verificar migraciones
python manage.py migrate --check
```

---

## Migraciones de Base de Datos

El proyecto usa Django Migrations para gestionar esquema de BD.

### Ver estado de migraciones

```bash
# Listar todas las migraciones
python manage.py showmigrations

# Ver migraciones pendientes
python manage.py migrate --plan

# Ejecutar migraciones pendientes
python manage.py migrate
```

### Información de migraciones actuales
- **Total**: 26 migraciones numeradas (`0001_initial.py` hasta `0026_*.py`)
- **Estado**: Todas debe estar marcadas con `[X]` (aplicadas)
- **Archivos**: Localizados en `empresa/migrations/`

### Si modificas modelos

```bash
# 1. Crear nueva migración automáticamente
python manage.py makemigrations

# 2. Revisar migración generada
cat empresa/migrations/00XX_auto_xxxx.py

# 3. Aplicar migración
python manage.py migrate
```

⚠️ **NUNCA** borra migraciones existentes.

## Comandos útiles

```
bash
# Verificar configuración
python manage.py check

# Crear superusuario
python manage.py createsuperuser

# Recolectar archivos estáticos (producción)
python manage.py collectstatic

# Ejecutar pruebas
pytest                          # Todas las pruebas
pytest -m "not slow"            # Solo pruebas rápidas
pytest empresa/tests/test_modelos.py  # Solo modelos
pytest -x                       # Parar al primer fallo
```

## Estructura del proyecto

```
contafy/
├── core/               # Configuración de Django
├── empresa/            # Aplicación principal
│   ├── migrations/     # Migraciones de base de datos
│   ├── models.py      # Modelos de datos
│   ├── views.py       # Vistas
│   ├── services/      # Lógica de negocio
│   └── templates/     # Plantillas HTML
├── static/            # Archivos estáticos
├── templates/         # Plantillas base
├── scripts/          # Scripts auxiliares
├── db.sqlite3        # Base de datos SQLite (desarrollo)
├── requirements.txt  # Dependencias Python
└── manage.py         # Script de gestión Django
```

## Despliegue en producción

### Render.com
El proyecto está configurado para despliegue en Render. Verifica los archivos:
- `render.yaml`
- `render-build.sh`
- `Procfile`

### Heroku
El proyecto soporta despliegue en Heroku:
- `Procfile`
- `requirements.txt`

## Licencia

MIT

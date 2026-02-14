# DEPLOYMENT - Guía de Despliegue a Otra Máquina

**Propósito**: Reproducir exactamente el estado del proyecto en otra máquina.

---

## Perspectiva General

Este documento cubre:
- ✅ Despliegue a **otra máquina Windows/Linux/Mac**
- ✅ Despliegue a **servidores en la nube (Render, Heroku)**
- ✅ Despliegue con **datos existentes** (restaurar BD)
- ✅ Despliegue en **desarrollo** vs. **producción**

---

## ESCENARIO 1: Otra Máquina Local (Windows/Linux/Mac)

### Requisitos
- Git instalado
- Python 3.11+ instalado
- PostgreSQL (opcional, si deseas usar la misma BD que el original)
- Acceso al repositorio de código

### Pasos

#### 1. Clonar o sincronizar repositorio

```bash
# Si es primera vez:
git clone <tu-repo-url> contafy
cd contafy

# Si ya existe:
cd contafy
git pull origin main
```

#### 2. Crear entorno virtual y instalar dependencias

```bash
# Crear entorno virtual
python -m venv .venv

# Activar (Windows):
.venv\Scripts\activate
# O activar (Linux/Mac):
source .venv/bin/activate

# Instalar dependencias
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configurar variables de entorno

```bash
# Copiar plantilla
cp .env.example .env

# Editar .env con credenciales locales
# Windows: notepad .env
# Linux/Mac: nano .env
```

Ejemplo de `.env` para desarrollo local:

```dotenv
DEBUG=True
SECRET_KEY=mi-clave-secreta-temporal-desarrollo
ALLOWED_HOSTS=localhost,127.0.0.1

# Opción A: SQLite (simple, sin BD externa)
# DATABASE_URL=  # Dejar vacío

# Opción B: PostgreSQL (si tienes servidor corriendo)
DATABASE_URL=postgres://usuario:password@localhost:5432/contafy_db
```

#### 4. Aplicar migraciones

```bash
python manage.py migrate
```

#### 5. Crear superusuario (si es BD nueva)

```bash
python manage.py createsuperuser
# Pide username, email, password
```

#### 6. Ejecutar servidor

```bash
python manage.py runserver
# Accede a http://127.0.0.1:8000
# Admin: http://127.0.0.1:8000/admin
```

---

## ESCENARIO 2: Restaurar Datos de BD Existente

Si el original generó un respaldo (`backup.sql`):

### Prerequisitos
- Archivo `backup.sql` (obtener del repositorio o compartido)
- PostgreSQL instalado y corriendo

### Pasos

#### 1. Preparar base de datos PostgreSQL

```bash
# Conectar como usuario admin (postgres)
psql -U postgres

# Dentro de psql shell (psql#):
CREATE DATABASE contafy_db;
CREATE USER contafy_user WITH PASSWORD 'mi_password';
ALTER ROLE contafy_user SET client_encoding TO 'utf8';
ALTER ROLE contafy_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE contafy_user SET default_transaction_deferrable TO on;
ALTER ROLE contafy_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE contafy_db TO contafy_user;
\q  # Salir
```

#### 2. Restaurar datos

```bash
# Restaurar desde respaldo
psql -U contafy_user -d contafy_db < backup.sql
# Pedirá contraseña

# Verificar conexión
psql -U contafy_user -d contafy_db -c "SELECT COUNT(*) FROM empresa_empresa;"
# Debería retornar cantidad de empresas
```

#### 3. Configurar .env

```dotenv
DEBUG=True
SECRET_KEY=mi-clave-secreta-temporal-desarrollo
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgres://contafy_user:mi_password@localhost:5432/contafy_db
```

#### 4. Aplicar migraciones (por seguridad)

```bash
python manage.py migrate
```

#### 5. Ejecutar servidor

```bash
python manage.py runserver
```

Los datos restaurados deberían estar disponibles inmediatamente.

---

## ESCENARIO 3: Despliegue a Render (Producción)

**Render** es un hosting en la nube similar a Heroku, pero más moderno.

### Prerequisitos
- Cuenta en [render.com](https://render.com)
- Repositorio en GitHub (público o privado con acceso a Render)
- PG de pago en Render (Postgres Database service)

### Pasos

#### 1. Crear PostgreSQL Database en Render

1. Iniciar sesión en [render.com](https://render.com)
2. New + → PostgreSQL
3. Nombre: `contafy-db`
4. Plan: Starter (gratuito si tienes créditos)
5. Copiar credenciales de conexión
6. Nota: `DATABASE_URL` aparecerá en la consola

#### 2. Crear Web Service en Render

1. New + → Web Service
2. Conectar repositorio GitHub
3. Configuración:
   - Name: `contafy-app`
   - Runtime: `Python 3.11`
   - Build Command: `bash render-build.sh` (ya existe en repo)
   - Start Command: `gunicorn core.wsgi:application --bind 0.0.0.0:8000`

#### 3. Configurar variables de entorno en Render

En la consola, ir a **Environment** y añadir:

```
DEBUG=False
SECRET_KEY=<generar-clave-fuerte-diferente-a-desarrollo>
ALLOWED_HOSTS=contafy-app.onrender.com
DATABASE_URL=postgresql://usuario:password@host:5432/nombre_db  # Del PostgreSQL
RENDER=true
```

#### 4. Desplegar

1. Click en "Deploy" en la consola de Render
2. Esperar a que se complete (5-15 minutos)
3. Ver logs en "Logs" tab
4. Acceder a `https://contafy-app.onrender.com`

#### 5. Crear superusuario en Render

```bash
# Abrir shell en Render:
# Console → Shell tab

python manage.py createsuperuser
# Pide username, email, password
```

#### 6. Restaurar datos (opcional)

Si tienes `backup.sql`:

```bash
# En Render Console:
psql postgresql://usuario:password@host/nombre_db < backup.sql
```

---

## ESCENARIO 4: Despliegue a Heroku (Alternativa)

Similar a Render, pero con Heroku:

### Pasos rápidos

```bash
# 1. Instalar Heroku CLI
# Descargar desde https://devcenter.heroku.com/articles/heroku-cli

# 2. Autenticarse
heroku login

# 3. Crear app
heroku create contafy-app

# 4. Crear PostgreSQL addon
heroku addons:create heroku-postgresql:hobby-dev -a contafy-app

# 5. Configurar variables
heroku config:set DEBUG=False SECRET_KEY=<clave> -a contafy-app
heroku config:set ALLOWED_HOSTS=contafy-app.herokuapp.com -a contafy-app

# 6. Desplegar
git push heroku main

# 7. Ver logs
heroku logs --tail -a contafy-app

# 8. Crear superusuario
heroku run python manage.py createsuperuser -a contafy-app
```

---

## CHECKLIST DE DESPLIEGUE

Antes de desplegar a otra máquina:

### En la máquina original
- [ ] `git status` muestra repositorio limpio
- [ ] `.env` NO está en Git
- [ ] `.venv/` NO está en Git
- [ ] `requirements.txt` tiene todas las dependencias con versiones fijas
- [ ] Todas las migraciones están aplicadas: `python manage.py showmigrations | grep '\[X\]'`
- [ ] Tests pasan: `python manage.py test empresa` (si existen)
- [ ] BD está respaldada: `pg_dump > backup.sql` (si tienes datos importantes)

### En la máquina receptora
- [ ] Python versión correcta (`python --version`)
- [ ] Git clonado correctamente (`git status`)
- [ ] `.venv` creado correctamente (`ls .venv/Scripts/python.exe`)
- [ ] Dependencias instaladas (`pip list | grep Django`)
- [ ] `requirements.txt` actualizado en el clone (`cat requirements.txt`)
- [ ] `.env` creado y configurado (`cat .env` - solo verificar que EXISTS)
- [ ] Migraciones aplicadas (`python manage.py migrate --check` sin errores)
- [ ] Servidor inicia sin errores (`python manage.py runserver`)
- [ ] Datos accesibles (si fue restaurado)

---

## Problemas Comunes

### Error: "ModuleNotFoundError: No module named 'django'"
```bash
# Verificar que .venv está activado
which python  # Linux/Mac
where python  # Windows

# Debe mostrar ruta dentro de .venv
# Si no, activar: source .venv/bin/activate (Linux/Mac)
#                 .venv\Scripts\activate (Windows)
```

### Error: "database 'contafy_db' does not exist"
```bash
# Opción A: Créala
createdb -U postgres contafy_db
python manage.py migrate

# Opción B: Usa SQLite (más simple)
# Comenta DATABASE_URL en .env
```

### Error: "DisallowedHost at /"
```django
# En .env, actualiza ALLOWED_HOSTS:
# LOCAL: ALLOWED_HOSTS=localhost,127.0.0.1
# RENDER: ALLOWED_HOSTS=contafy-app.onrender.com
# HEROKU: ALLOWED_HOSTS=contafy-app.herokuapp.com
```

### Error: "CSRF verification failed"
```python
# En .env asegura:
# DEBUG=False (en producción)
# SECRET_KEY diferente a desarrollo
# ALLOWED_HOSTS configurado correctamente
```

---

## Verificación Post-Despliegue

1. **Acceso web**: Abre `http://127.0.0.1:8000` o dominio en producción
2. **Admin Django**: `/admin` - login con superusuario
3. **API REST**: `/api/` - si está configurada
4. **Logs**: Busca errores en `python manage.py runserver --verbosity 3`
5. **BD**: Verifica datosestán presentes: `python manage.py shell` y querys

---

## Git Workflow para Mantener Sincronizado

```bash
# En máquina original (después de cambios):
git add .
git commit -m "descripción del cambio"
git push origin main

# En máquina receptora (traer cambios):
git pull origin main
python manage.py migrate  # Si hay nuevas migraciones
# Reiniciar servidor si estaba corriendo
```

---

## Automatización con Scripts

Se incluyen dos scripts para automatizar los pasos:

- **Linux/Mac**: `bash setup.sh` - Automatiza pasos 1-9
- **Windows PowerShell**: `powershell -ExecutionPolicy Bypass -File setup.ps1`

Uso:
```bash
bash setup.sh
# Sigue las instrucciones interactivas
```

---

## Conclusión

**CONTAFY** está diseñado para ser reproducible:
- ✅ Requirements.txt con versiones fijas
- ✅ Migraciones Django completas
- ✅ .env.example documentado
- ✅ Scripts de automatización
- ✅ Documentación clara

Para cualquier problema, revisar logs y SETUP.md.

**Última actualización**: 2026-02-13


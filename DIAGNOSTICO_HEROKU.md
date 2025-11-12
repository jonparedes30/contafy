# 🔍 DIAGNÓSTICO HEROKU - CONTAFY
## Guía para Resolver Problemas de Deploy

**Fecha:** 2025
**Problema:** Sistema no abre en Heroku

---

## PASO 1: Verificar Logs de Heroku

```bash
# Ver logs en tiempo real
heroku logs --tail --app contafy-pruebas

# Ver últimos 200 logs
heroku logs -n 200 --app contafy-pruebas

# Buscar errores específicos
heroku logs --app contafy-pruebas | grep -i error
```

---

## PROBLEMAS COMUNES Y SOLUCIONES

### 1. ❌ SECRET_KEY No Configurada

**Error:**
```
ValueError: SECRET_KEY debe ser configurada en .env
```

**Solución:**
```bash
# Generar nueva SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(50))"

# Configurar en Heroku
heroku config:set SECRET_KEY="tu_secret_key_generada" --app contafy-pruebas
```

---

### 2. ❌ DATABASE_URL No Configurada

**Error:**
```
django.core.exceptions.ImproperlyConfigured: settings.DATABASES is improperly configured
```

**Solución:**
```bash
# Verificar que Postgres está provisionado
heroku addons --app contafy-pruebas

# Si no existe, agregar Postgres
heroku addons:create heroku-postgresql:mini --app contafy-pruebas

# Verificar DATABASE_URL
heroku config:get DATABASE_URL --app contafy-pruebas
```

---

### 3. ❌ Migraciones No Aplicadas

**Error:**
```
django.db.utils.ProgrammingError: relation "empresa_usuario" does not exist
```

**Solución:**
```bash
# Ejecutar migraciones manualmente
heroku run python manage.py migrate --app contafy-pruebas

# Verificar estado de migraciones
heroku run python manage.py showmigrations --app contafy-pruebas
```

---

### 4. ❌ Archivos Estáticos No Recolectados

**Error:**
```
404 Not Found: /static/...
```

**Solución:**
```bash
# Recolectar estáticos manualmente
heroku run python manage.py collectstatic --noinput --app contafy-pruebas

# Verificar que WhiteNoise está instalado
heroku run pip list | grep whitenoise --app contafy-pruebas
```

---

### 5. ❌ Gunicorn No Instalado

**Error:**
```
bash: gunicorn: command not found
```

**Solución:**
```bash
# Verificar requirements.txt incluye gunicorn
cat requirements.txt | grep gunicorn

# Si no está, agregarlo
echo "gunicorn==21.2.0" >> requirements.txt
git add requirements.txt
git commit -m "add gunicorn"
git push heroku main
```

---

### 6. ❌ Puerto Incorrecto

**Error:**
```
Error R10 (Boot timeout) -> Web process failed to bind to $PORT within 60 seconds
```

**Problema:** Gunicorn no está escuchando en el puerto correcto

**Solución en Procfile:**
```
web: gunicorn core.wsgi --bind 0.0.0.0:$PORT --log-file -
```

---

### 7. ❌ ALLOWED_HOSTS Incorrecto

**Error:**
```
DisallowedHost at / Invalid HTTP_HOST header
```

**Solución:**
```bash
# Verificar configuración actual
heroku config:get ALLOWED_HOSTS --app contafy-pruebas

# Configurar correctamente
heroku config:set ALLOWED_HOSTS="contafy-pruebas-30fdb804cc25.herokuapp.com,.herokuapp.com" --app contafy-pruebas
```

---

## VERIFICACIÓN COMPLETA

### Paso 1: Verificar Variables de Entorno

```bash
# Ver todas las variables
heroku config --app contafy-pruebas

# Variables REQUERIDAS:
# - SECRET_KEY
# - DATABASE_URL (automática con Postgres)
# - ALLOWED_HOSTS
# - DEBUG=False
```

### Paso 2: Verificar Procfile

**Archivo:** `Procfile`
```
release: python manage.py migrate
web: gunicorn core.wsgi --log-file -
```

### Paso 3: Verificar runtime.txt

**Archivo:** `runtime.txt`
```
python-3.11.10
```

### Paso 4: Verificar requirements.txt

**Debe incluir:**
```
Django>=4.2,<5.0
gunicorn>=21.2.0
whitenoise>=6.5.0
psycopg2-binary>=2.9.9
django-environ>=0.11.2
djangorestframework>=3.14.0
djangorestframework-simplejwt>=5.3.0
```

---

## COMANDOS DE DIAGNÓSTICO

### 1. Estado de la Aplicación
```bash
heroku ps --app contafy-pruebas
```

**Salida esperada:**
```
=== web (Free): gunicorn core.wsgi --log-file - (1)
web.1: up 2025/01/12 10:00:00 -0500 (~ 1h ago)
```

### 2. Verificar Dyno
```bash
heroku ps:scale web=1 --app contafy-pruebas
```

### 3. Reiniciar Aplicación
```bash
heroku restart --app contafy-pruebas
```

### 4. Abrir Aplicación
```bash
heroku open --app contafy-pruebas
```

### 5. Ejecutar Shell
```bash
heroku run python manage.py shell --app contafy-pruebas
```

### 6. Verificar Base de Datos
```bash
heroku pg:info --app contafy-pruebas
heroku pg:psql --app contafy-pruebas
```

---

## CONFIGURACIÓN MÍNIMA REQUERIDA

### Variables de Entorno en Heroku

```bash
# 1. SECRET_KEY (OBLIGATORIO)
heroku config:set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" --app contafy-pruebas

# 2. DEBUG (OBLIGATORIO)
heroku config:set DEBUG=False --app contafy-pruebas

# 3. ALLOWED_HOSTS (OBLIGATORIO)
heroku config:set ALLOWED_HOSTS="contafy-pruebas-30fdb804cc25.herokuapp.com,.herokuapp.com" --app contafy-pruebas

# 4. DJANGO_SETTINGS_MODULE (opcional, por defecto usa core.settings)
heroku config:set DJANGO_SETTINGS_MODULE=core.settings --app contafy-pruebas

# 5. Verificar DATABASE_URL (automática con Postgres addon)
heroku config:get DATABASE_URL --app contafy-pruebas
```

---

## SOLUCIÓN RÁPIDA (SCRIPT COMPLETO)

```bash
#!/bin/bash
# Script de configuración rápida para Heroku

APP_NAME="contafy-pruebas"

echo "🔧 Configurando Heroku para $APP_NAME..."

# 1. Generar y configurar SECRET_KEY
echo "📝 Generando SECRET_KEY..."
SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(50))')
heroku config:set SECRET_KEY="$SECRET_KEY" --app $APP_NAME

# 2. Configurar DEBUG
echo "🐛 Configurando DEBUG=False..."
heroku config:set DEBUG=False --app $APP_NAME

# 3. Configurar ALLOWED_HOSTS
echo "🌐 Configurando ALLOWED_HOSTS..."
heroku config:set ALLOWED_HOSTS="contafy-pruebas-30fdb804cc25.herokuapp.com,.herokuapp.com" --app $APP_NAME

# 4. Verificar Postgres
echo "🗄️ Verificando Postgres..."
heroku addons --app $APP_NAME | grep postgres || heroku addons:create heroku-postgresql:mini --app $APP_NAME

# 5. Ejecutar migraciones
echo "📊 Ejecutando migraciones..."
heroku run python manage.py migrate --app $APP_NAME

# 6. Recolectar estáticos
echo "📦 Recolectando archivos estáticos..."
heroku run python manage.py collectstatic --noinput --app $APP_NAME

# 7. Reiniciar aplicación
echo "🔄 Reiniciando aplicación..."
heroku restart --app $APP_NAME

# 8. Verificar estado
echo "✅ Verificando estado..."
heroku ps --app $APP_NAME

# 9. Ver logs
echo "📋 Mostrando logs..."
heroku logs --tail --app $APP_NAME
```

---

## CHECKLIST DE VERIFICACIÓN

### Pre-Deploy
- [ ] `SECRET_KEY` generada y configurada
- [ ] `DEBUG=False` en producción
- [ ] `ALLOWED_HOSTS` incluye dominio de Heroku
- [ ] `requirements.txt` actualizado
- [ ] `Procfile` correcto
- [ ] `runtime.txt` especifica Python 3.11+
- [ ] Postgres addon provisionado

### Post-Deploy
- [ ] Migraciones aplicadas
- [ ] Archivos estáticos recolectados
- [ ] Dyno web corriendo
- [ ] Aplicación responde en navegador
- [ ] Login funciona
- [ ] No hay errores en logs

---

## ERRORES ESPECÍFICOS DE CONTAFY

### Error: "SECRET_KEY debe ser configurada en .env"

**Causa:** `settings.py` línea 18-19 valida SECRET_KEY

**Solución:**
```python
# En settings.py, cambiar:
if not SECRET_KEY or SECRET_KEY == 'clave_de_prueba_contafy':
    raise ValueError("SECRET_KEY debe ser configurada en .env")

# Por (temporal para debug):
if not SECRET_KEY:
    SECRET_KEY = env('SECRET_KEY', default=secrets.token_urlsafe(50))
    print(f"WARNING: Using auto-generated SECRET_KEY")
```

O mejor, configurar en Heroku:
```bash
heroku config:set SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(50))')" --app contafy-pruebas
```

---

## MONITOREO POST-DEPLOY

### 1. Verificar Salud de la App
```bash
# Cada 5 minutos durante la primera hora
watch -n 300 'heroku ps --app contafy-pruebas'
```

### 2. Monitorear Logs
```bash
heroku logs --tail --app contafy-pruebas | tee heroku-logs.txt
```

### 3. Verificar Métricas
```bash
heroku metrics --app contafy-pruebas
```

### 4. Verificar Base de Datos
```bash
heroku pg:info --app contafy-pruebas
```

---

## CONTACTO Y SOPORTE

### Heroku Support
- Dashboard: https://dashboard.heroku.com/apps/contafy-pruebas
- Docs: https://devcenter.heroku.com/
- Status: https://status.heroku.com/

### Comandos de Emergencia
```bash
# Rollback a versión anterior
heroku releases --app contafy-pruebas
heroku rollback v123 --app contafy-pruebas

# Escalar dyno
heroku ps:scale web=0 --app contafy-pruebas  # Apagar
heroku ps:scale web=1 --app contafy-pruebas  # Encender

# Modo mantenimiento
heroku maintenance:on --app contafy-pruebas
heroku maintenance:off --app contafy-pruebas
```

---

## PRÓXIMOS PASOS

1. **Ejecutar diagnóstico:**
   ```bash
   heroku logs -n 200 --app contafy-pruebas
   ```

2. **Identificar error específico** en los logs

3. **Aplicar solución** correspondiente de esta guía

4. **Verificar** que la aplicación funciona

5. **Documentar** cualquier problema nuevo encontrado

---

**Última actualización:** 2025
**Mantenido por:** Amazon Q Developer

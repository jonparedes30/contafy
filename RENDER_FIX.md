# Solución para Deploy en Render - CONTAFY

## Problemas Identificados y Soluciones

### 1. CRÍTICO: Usuario sin Empresa
**Problema**: `create_superuser` falla porque Usuario requiere Empresa.

**Solución**: Modificar `docker-entrypoint.sh`:

```bash
# Reemplazar sección de superusuario con:
python manage.py shell << 'END'
from django.contrib.auth import get_user_model
from empresa.models import Empresa
import os

User = get_user_model()
username = os.environ.get('ADMIN_USERNAME', 'admin')
email = os.environ.get('ADMIN_EMAIL', 'admin@contafy.com')
password = os.environ.get('ADMIN_PASSWORD', 'changeme123')

if not User.objects.filter(username=username).exists():
    # Crear empresa primero
    empresa, _ = Empresa.objects.get_or_create(
        ruc='9999999999001',
        defaults={
            'nombre': 'Empresa Demo',
            'direccion': 'Ecuador',
            'categoria': 'comercial'
        }
    )
    # Crear superusuario con empresa
    user = User.objects.create_superuser(username, email, password)
    user.empresa = empresa
    user.save()
    print(f'✅ Superusuario {username} creado con empresa')
else:
    print(f'ℹ️ Superusuario {username} ya existe')
END
```

### 2. CRÍTICO: Dependencias Pesadas
**Problema**: Pandas/Matplotlib causan timeout en build.

**Solución**: Crear `requirements-render.txt` optimizado:

```txt
Django==5.2.3
django-environ==0.12.0
djangorestframework==3.16.0
djangorestframework_simplejwt==5.5.0
django-jazzmin==3.0.0
gunicorn==21.2.0
psycopg2-binary==2.9.10
whitenoise==6.6.0
dj-database-url==2.1.0
pillow==11.3.0
requests==2.32.4
pytz==2025.2
# Remover pandas, matplotlib, openpyxl, xlsxwriter, reportlab temporalmente
```

Actualizar `Dockerfile`:
```dockerfile
COPY requirements-render.txt requirements.txt
```

### 3. MEDIO: ALLOWED_HOSTS
**Problema**: Dominio de Render no permitido.

**Solución**: Modificar `settings.py`:

```python
# Reemplazar línea 25
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    'localhost', 
    '127.0.0.1', 
    '.herokuapp.com',
    '.onrender.com'  # AGREGAR ESTO
])
```

### 4. MEDIO: SECRET_KEY
**Problema**: Puede no generarse correctamente.

**Solución**: En `render.yaml`, asegurar:

```yaml
envVars:
  - key: SECRET_KEY
    generateValue: true  # Ya está, pero verificar en dashboard
```

O generar manualmente:
```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```
Y agregarlo en Render Dashboard.

### 5. BAJO: Optimizar Dockerfile
**Problema**: Build lento.

**Solución**: Usar multi-stage build:

```dockerfile
FROM python:3.12-slim as builder

WORKDIR /app
COPY requirements-render.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements-render.txt

FROM python:3.12-slim

WORKDIR /app
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

COPY . .
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]
```

### 6. BAJO: Health Check
**Problema**: `/health/` puede no existir.

**Solución**: Crear vista health en `empresa/views/health.py`:

```python
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return JsonResponse({'status': 'healthy', 'database': 'connected'})
    except Exception as e:
        return JsonResponse({'status': 'unhealthy', 'error': str(e)}, status=503)
```

Agregar en `core/urls.py`:
```python
from empresa.views.health import health_check

urlpatterns = [
    path('health/', health_check, name='health'),
    # ... resto
]
```

## Orden de Implementación

1. ✅ Crear `requirements-render.txt` (sin pandas/matplotlib)
2. ✅ Modificar `docker-entrypoint.sh` (crear empresa antes de usuario)
3. ✅ Actualizar `settings.py` (agregar .onrender.com a ALLOWED_HOSTS)
4. ✅ Crear vista `/health/`
5. ✅ Verificar SECRET_KEY en Render Dashboard
6. ✅ Hacer commit y push
7. ✅ Redeploy en Render

## Comandos para Aplicar

```bash
# 1. Crear requirements optimizado
cat > requirements-render.txt << 'EOF'
Django==5.2.3
django-environ==0.12.0
djangorestframework==3.16.0
djangorestframework_simplejwt==5.5.0
django-jazzmin==3.0.0
gunicorn==21.2.0
psycopg2-binary==2.9.10
whitenoise==6.6.0
dj-database-url==2.1.0
pillow==11.3.0
requests==2.32.4
pytz==2025.2
EOF

# 2. Commit cambios
git add .
git commit -m "fix: Optimizar deploy para Render"
git push origin main
```

## Verificación Post-Deploy

```bash
# Verificar logs en Render Dashboard
# Buscar:
# ✅ Migraciones exitosas
# ✅ Superusuario creado
# ✅ Gunicorn iniciado
# ✅ Health check respondiendo

# Probar endpoints:
curl https://tu-app.onrender.com/health/
curl https://tu-app.onrender.com/app-beta-2024/login/
```

## Notas Importantes

- **Plan Starter**: 512MB RAM, puede ser insuficiente con pandas/matplotlib
- **Build Time**: Máximo 15 minutos, optimizar dependencias
- **Database**: PostgreSQL incluido en plan Starter
- **Logs**: Revisar en Dashboard > Logs para debugging

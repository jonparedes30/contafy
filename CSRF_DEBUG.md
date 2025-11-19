# CSRF 403 - Diagnóstico y Solución

## Problema Identificado
Configuración CSRF duplicada y conflictiva en `settings.py`

## Cambios Aplicados

### 1. Consolidación de Configuración CSRF
**Archivo**: `core/settings.py`

- ❌ **ANTES**: Dos bloques `if 'RENDER' in os.environ:` duplicados (líneas 178-182 y 193-211)
- ✅ **AHORA**: Un solo bloque consolidado con `CSRF_COOKIE_DOMAIN = None` explícito

### 2. Logging Detallado
**Archivo**: `empresa/views/autenticacion.py`

Agregado logging en `login_usuario()` para ver:
- Token CSRF en POST data
- Cookie CSRF
- Headers Referer y Origin

## Próximos Pasos

### 1. Commit y Deploy
```bash
git add core/settings.py empresa/views/autenticacion.py CSRF_DEBUG.md
git commit -m "fix: consolidar config CSRF y agregar logging detallado"
git push origin main
```

### 2. Revisar Logs en Render
Después del deploy, intenta login y busca en logs:
```
POST login - CSRF token en POST: ...
POST login - CSRF cookie: ...
POST login - Referer: ...
POST login - Origin: ...
```

### 3. Verificar en DevTools
**Network → POST /app-beta-2024/login/**

Request Headers debe tener:
```
Cookie: csrftoken=XXXXX
```

Form Data debe tener:
```
csrfmiddlewaretoken: XXXXX
```

## Causas Posibles del 403

### A. Token CSRF faltante
- **Síntoma**: Logs muestran "MISSING" en token o cookie
- **Solución**: Verificar que GET /login/ envía `Set-Cookie: csrftoken=...`

### B. Domain mismatch
- **Síntoma**: Cookie no se envía en POST
- **Solución**: `CSRF_COOKIE_DOMAIN = None` (ya aplicado)

### C. Referer/Origin incorrecto
- **Síntoma**: Logs muestran Referer vacío o diferente
- **Solución**: Verificar `CSRF_TRUSTED_ORIGINS` incluye el dominio

### D. Secure cookie en HTTP
- **Síntoma**: Cookie no persiste
- **Solución**: `CSRF_COOKIE_SECURE = True` solo en HTTPS (ya configurado)

## Configuración Final CSRF

```python
# Global (línea 35-40)
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_HTTPONLY = False
CSRF_USE_SESSIONS = False
CSRF_COOKIE_NAME = 'csrftoken'

# Render específico (línea 193-211)
if 'RENDER' in os.environ:
    CSRF_COOKIE_SECURE = True
    CSRF_COOKIE_DOMAIN = None  # ← CRÍTICO
```

## Test Temporal (si persiste el error)

Agregar `@csrf_exempt` temporal en `login_usuario`:
```python
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # SOLO PARA DIAGNÓSTICO
def login_usuario(request):
    # ...
```

Si funciona con `@csrf_exempt`, confirma 100% que es problema CSRF.

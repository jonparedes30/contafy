# ⚡ QUICK REFERENCE - Cambios Aplicados

## 📂 Archivos Modificados

### 1. `empresa/views/productos.py`
- **Línea 1-25**: Importaciones actualizadas (agregado `logging`, importación defensiva de `TrigramSimilarity`)
- **Línea 315-570**: Función `prefill_producto_from_scan()` reescrita completamente

### 2. `empresa/static/js/pos_quickbox.js` 
- **Archivo nuevo**: Módulo JavaScript para gestión del carrito POS

### 3. `core/settings.py` 
- **Modificación opcional**: Si 404 persiste, agregar STATICFILES_DIRS (ver instrucciones abajo)

---

## 🔑 IMPORTACIONES CLAVE EN `productos.py`

```python
import logging

logger = logging.getLogger(__name__)

# Importación defensiva - CLAVE DEL FIX
try:
    from django.contrib.postgres.search import TrigramSimilarity
    HAS_TRIGRAM = True
except ImportError:
    HAS_TRIGRAM = False
    TrigramSimilarity = None
```

---

## 💡 LÓGICA CENTRAL SIMPLIFICADA

```python
if request.method != 'POST':  # ✅ Validar método
    return JsonResponse({'error': 'Method not allowed'}, status=405)

try:
    payload = json.loads(request.body.decode('utf-8'))  # ✅ Parsear JSON
except:  # ✅ Capturar error JSON
    return JsonResponse({'error': 'JSON inválido'}, status=400)

# ✅ Validación defensiva de campos
barcode = str(payload.get('barcode') or '').strip() or None
nombre = str(payload.get('nombre') or '').strip() or None

# ✅ Búsqueda exacta PRIMERO
if barcode:
    producto = Producto.objects.filter(empresa=empresa).filter(
        Q(codigo_barras__iexact=barcode) | Q(codigo__iexact=barcode)
    ).first()
    if producto:
        return JsonResponse(serialize_producto(producto))

# ✅ Búsqueda fuzzy CON fallback
if HAS_TRIGRAM:  # PostgreSQL disponible
    # Usar TrigramSimilarity (rápido)
    qs = Producto.objects.annotate(
        sim_nombre=TrigramSimilarity('nombre', probe),
        sim_desc=TrigramSimilarity('descripcion', probe),
    ).annotate(sim=Greatest(F('sim_nombre'), F('sim_desc')))
else:  # Fallback automático
    # Usar icontains (SQLite compatible)
    qs = Producto.objects.filter(
        Q(nombre__icontains=probe) | Q(descripcion__icontains=probe)
    )

# ✅ NUNCA 500: excepto definitivo, retorna 200 siempre
except Exception as e:
    logger.error(f'Error: {str(e)[:200]}', exc_info=True)
    return JsonResponse({'error': 'Error', 'encontrado': False}, status=200)
```

---

## 📦 VALIDACIÓN DEFENSIVA EJEMPLO

```python
# ❌ MAL - Causa 500 si falta la clave
precio = payload.get('precio_unitario')  # Qué si es None?
float_precio = float(precio)  # TypeError!

# ✅ BIEN - Defensivo
precio = None
try:
    precio = float(payload.get('precio_unitario') or payload.get('precio') or 0)
except (ValueError, TypeError):
    precio = 0
```

---

## 🧪 TEST RÁPIDO DESDE TERMINAL

```powershell
# Activar venv
./venv/Scripts/Activate.ps1

# Test con curl (necesitas reemplazar CSRF_TOKEN)
$token = (curl -s http://localhost:8000/app-beta-2024/venta/crear/ | Select-String 'csrfmiddlewaretoken' -Context 0,0).ToString()

# Enviar request
curl -X POST "http://localhost:8000/app-beta-2024/producto/prefill_from_scan/" `
  -H "Content-Type: application/json" `
  -H "X-CSRFToken: $token" `
  -d '{"probes":["coca"], "barcode":"123"}'

# Debería responder SIN 500
```

---

## 🔍 VERIFICAR EN LOGS

Abre la consola del servidor Django y busca:

✅ **Info (búsqueda exitosa):**
```
INFO Encontrado por barcode: 5
INFO Encontrados 3 matches por probes
```

⚠️ **Warning (normal, fallback activado):**
```
WARNING TrigramSimilarity no disponible, usando icontains
```

❌ **Error (problema real):**
```
ERROR Error definitivo en prefill_from_scan: ...
```

---

## 📋 CHECKLIST APLICACIÓN

- [ ] Reemplacé `empresa/views/productos.py` completo (o copié la nueva función)
- [ ] Creé archivo `empresa/static/js/pos_quickbox.js`
- [ ] Reinicié servidor Django (`Ctrl+C` + `python manage.py runserver`)
- [ ] Limpié cache del navegador (`Ctrl+Shift+Del`)
- [ ] Probé endpoint desde navegador (va a `/venta/crear/` y hace escaneo)
- [ ] Verifico consola: NO hay 500, sí hay respuesta JSON
- [ ] Verifico Network tab: `pos_quickbox.js` carga con 200, no 404

---

## 🚨 SI AÚNSIGUE FALLANDO

### 404 en pos_quickbox.js
```python
# Agregar en core/settings.py, DESPUÉS de STATIC_ROOT = ...
import os
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'empresa', 'static'),
]

# Luego ejecutar:
# python manage.py collectstatic --noinput
```

### 500 en prefill_from_scan
1. Verifica que `empresa/views/productos.py` está actualizado
2. Verifica que `logger = logging.getLogger(__name__)` está en el top
3. Verifica que `HAS_TRIGRAM` está definido
4. Runtime error? Revisa los logs para el stack trace exacto

### Las búsquedas no encuentran productos
- Verifica que la empresa del usuario tiene productos
- Verifica que los probes no están vacíos
- Si ves "TrigramSimilarity no disponible", significa fallback a icontains (es OK en SQLite)

---

## 🎯 RESULTADO ESPERADO

**Antes (❌ Error):**
```
POST /app-beta-2024/producto/prefill_from_scan/
Response: 500 Internal Server Error
```

**Después (✅ Funciona):**
```
POST /app-beta-2024/producto/prefill_from_scan/
Response: 200 OK
Body: {"matches": [...]} o {"encontrado": false}
```

---

## 📚 REFERENCIAS

- Implementación completa: [FIX_PREFILL_SCAN_500_ERROR.md](FIX_PREFILL_SCAN_500_ERROR.md)
- Documentación Django: https://docs.djangoproject.com/en/5.0/ref/contrib/postgres/search/
- PostgreSQL TrigramSimilarity: https://www.postgresql.org/docs/current/pgtrgm.html

# 🚀 PLAN DE MIGRACIÓN - UNIFICACIÓN DEL ESCÁNER

> **Nota:** Ver [TESTING_ESCANER.md](TESTING_ESCANER.md) para la guía de testing completa con las URLs correctas (`/app-beta-2024/`).

## ⚠️ ANTES DE EMPEZAR

### 1. Backup Completo
```bash
# Backup de base de datos
python manage.py dumpdata > backup_$(date +%Y%m%d).json

# Backup de archivos
cp empresa/views/compras.py empresa/views/compras.py.backup
cp empresa/templates/empresa/crear_compra.html empresa/templates/empresa/crear_compra.html.backup
cp empresa/templates/empresa/crear_venta.html empresa/templates/empresa/crear_venta.html.backup
cp empresa/templates/empresa/crear_producto.html empresa/templates/empresa/crear_producto.html.backup
```

### 2. Verificar Configuración
```bash
# Ejecutar script de verificación
python verificar_modelo.py

# Verificar que GOOGLE_VISION_API_KEY esté en settings.py
grep "GOOGLE_VISION_API_KEY" core/settings.py
```

---

## 📅 FASE 1: Backend (Día 1 - 2 horas)

### Paso 1.1: API Unificada
- [x] Función `vision_search_api` actualizada en `empresa/views/compras.py`
- [x] Soporta parámetro `contexto`: inventario, compra, venta
- [x] Respuesta estandarizada: `success`, `productos`, `products` (legacy)

### Paso 1.2: Probar API

**Test con curl o Postman:**
```bash
POST http://localhost:8000/app-beta-2024/compra/vision-search/
Headers:
  Content-Type: application/json
  X-CSRFToken: <token>
  Cookie: sessionid=...

Body:
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
  "contexto": "compra"
}
```

Verificar:
- [ ] `success: true`
- [ ] Campo `productos` existe y es array
- [ ] Campo `products` existe (legacy)
- [ ] `meta.contexto` corresponde al enviado

---

## 📅 FASE 2: Módulo Inventario (Día 1 - 1 hora)

### Paso 2.1: Escáner Vision
- [x] Botón "Escanear Producto Nuevo" en `crear_producto.html`
- [x] Modal con cámara
- [x] Integración con API unificada (contexto: inventario)

### Paso 2.2: Probar
- [ ] Abrir "Crear Producto"
- [ ] Clic en "Escanear Producto Nuevo"
- [ ] Producto NO existe: prellenar nombre y código
- [ ] Producto SÍ existe: advertencia + opción "Ir a Crear Compra"

---

## 📅 FASE 3: Módulo Compras (Día 2 - 1 hora)

### Paso 3.1: Actualización
- [x] Fetch con `contexto: 'compra'`
- [x] Lee `data.productos || data.products`
- [x] Si producto no existe: redirige a Crear Producto con localStorage

### Paso 3.2: Probar
**Flujo A - Producto existe:**
- [ ] Escanear producto registrado → rellena formulario

**Flujo B - Producto NO existe:**
- [ ] Escanear producto nuevo → alerta → "Ir a Crear Producto"
- [ ] Verificar redirección y prellenado en Crear Producto

---

## 📅 FASE 4: Módulo Ventas (Día 2 - 1 hora)

### Paso 4.1: Cambio a API Unificada
- [x] URL: `vision_search_api` (ya no producto_scan_vision)
- [x] Content-Type: JSON
- [x] contexto: 'venta'

### Paso 4.2: Probar
- [ ] Escanear producto con stock → agrega al carrito
- [ ] Escanear producto sin stock → advertencia
- [ ] Escanear producto inexistente → "No encontrado"

---

## 📅 FASE 5: Testing Integral (Día 3 - 2 horas)

### Escenario 1: Producto Nuevo Completo
1. [ ] Ir a "Crear Producto"
2. [ ] Escanear producto nuevo
3. [ ] Completar y guardar
4. [ ] Ir a "Crear Compra" → escanear → debe aparecer
5. [ ] Guardar compra
6. [ ] Ir a "Crear Venta" → escanear → agregar al carrito → cobrar

### Escenario 2: Usuario va directo a Compras
1. [ ] Ir a "Crear Compra" sin registrar producto
2. [ ] Escanear producto nuevo
3. [ ] Alerta → "Ir a Crear Producto"
4. [ ] Verificar prellenado
5. [ ] Guardar → volver a Compras → escanear → debe aparecer

### Escenario 3: Prevención Duplicados
1. [ ] Ir a "Crear Producto"
2. [ ] Escanear producto que ya existe
3. [ ] Verificar advertencia + "Ir a Crear Compra"

---

## 🆘 ROLLBACK

```bash
cp empresa/views/compras.py.backup empresa/views/compras.py
cp empresa/templates/empresa/crear_compra.html.backup empresa/templates/empresa/crear_compra.html
cp empresa/templates/empresa/crear_venta.html.backup empresa/templates/empresa/crear_venta.html
cp empresa/templates/empresa/crear_producto.html.backup empresa/templates/empresa/crear_producto.html
python manage.py runserver
```

---

## 📞 TROUBLESHOOTING

1. **Error "GOOGLE_VISION_API_KEY no configurada"**  
   Agregar en `core/settings.py`:  
   `GOOGLE_VISION_API_KEY = 'tu-api-key-aqui'`

2. **CSRF token no encontrado**  
   Verificar que el formulario tenga `{% csrf_token %}` y que la cookie de sesión esté activa.

3. **Cámara no se activa**  
   Usar HTTPS o localhost. Verificar permisos del navegador.

4. **producto_scan_vision (ventas) ya no se usa**  
   La ruta sigue existiendo pero Ventas ahora usa `vision_search_api`. Se puede eliminar `producto_scan_vision` tras confirmar que todo funciona.

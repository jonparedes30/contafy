# Guía de Testing - Escáner Unificado

## URLs correctas del proyecto

Base: `http://localhost:8000/app-beta-2024/`

| Módulo | URL completa |
|--------|--------------|
| API Escáner | `http://localhost:8000/app-beta-2024/compra/vision-search/` |
| Crear Producto | `http://localhost:8000/app-beta-2024/producto/crear/` |
| Crear Compra | `http://localhost:8000/app-beta-2024/compra/crear/` |
| Crear Venta | `http://localhost:8000/app-beta-2024/venta/crear/` |

---

## PASO 1: Verificar modelo (2 minutos)

```bash
python verificar_modelo.py
```

**Revisa la salida:**
- [OK] Todos los campos requeridos deben tener [OK]
- Si alguno tiene [X], necesitas agregarlo al modelo

---

## PASO 2: Testing básico del backend (15 minutos)

### Test 1: API responde correctamente

**Opción A - Con navegador:**
1. Abre: `http://localhost:8000/app-beta-2024/compra/vision-search/`
2. Debes ver error 405 "Solo se permite método POST" (correcto)

**Opción B - Con Postman/Insomnia:**
```
POST http://localhost:8000/app-beta-2024/compra/vision-search/

Headers:
  Content-Type: application/json

Body (raw JSON):
{
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA//2Q==",
  "contexto": "inventario"
}
```

**Respuesta esperada:**
```json
{
  "success": true,
  "ok": true,
  "found": false,
  "productos": [],
  "products": [],
  "codigo_detectado": "",
  "meta": {
    "total": 0,
    "contexto": "inventario",
    "api_version": "2.0"
  },
  "debug": {
    "logos": [],
    "textos": [],
    "labels": [],
    "texto_completo": "..."
  }
}
```

---

## PASO 3: Testing del flujo completo (30 minutos)

### Prepara antes de empezar
- Un producto físico con etiqueta visible (galletas, botella, caja)
- Cámara (celular o webcam)
- Sesión iniciada en la aplicación

---

### ESCENARIO 1: Flujo ideal - Usuario experto

#### Paso 1.1: Crear Producto
1. Abrir: `http://localhost:8000/app-beta-2024/producto/crear/`
2. Clic en "Escanear Producto Nuevo (Cámara + IA)"
3. Permitir acceso a la cámara
4. Enfocar el producto y clic en "DETECTAR PRODUCTO"

**Verificar:**
- [ ] Aparece "Producto nuevo detectado"
- [ ] Campo "Nombre" se llenó
- [ ] Campo "Código de barras" se llenó (si es visible)

5. Completar: Precio 10.00, PVP 15.00, Categoría, Stock inicial: 0
6. Guardar

**Verificar:**
- [ ] Se guardó sin errores
- [ ] Aparece en la lista de productos

#### Paso 1.2: Crear Compra
1. Abrir: `http://localhost:8000/app-beta-2024/compra/crear/`
2. Clic en "Abrir Aplicación de Escaneo"
3. Escanear EL MISMO PRODUCTO del paso anterior

**Verificar:**
- [ ] Aparece "Producto encontrado"
- [ ] Muestra nombre correcto, stock: 0, precio: 10.00
- [ ] Clic en "Usar este producto"
- [ ] Formulario se llenó automáticamente

5. Cambiar cantidad a 50 y guardar

**Verificar:**
- [ ] Compra guardada
- [ ] Stock del producto ahora es 50

#### Paso 1.3: Crear Venta
1. Abrir: `http://localhost:8000/app-beta-2024/venta/crear/`
2. Clic en "Escanear"
3. Escanear EL MISMO PRODUCTO

**Verificar:**
- [ ] Aparece en el carrito
- [ ] Precio: 15.00 (PVP)
- [ ] Finalizar venta

**Verificar:**
- [ ] Venta registrada
- [ ] Stock ahora es 49 (50 - 1)

---

### ESCENARIO 2: Usuario novato - Se equivoca

1. Abrir: `http://localhost:8000/app-beta-2024/compra/crear/`
2. Escanear un producto NO registrado

**Verificar:**
- [ ] Aparece "Producto no encontrado"
- [ ] Mensaje: "Debes registrarlo primero en Crear Producto"
- [ ] Botón "Ir a Crear Producto"

3. Clic en "Ir a Crear Producto"

**Verificar:**
- [ ] Redirige a producto/crear/
- [ ] Campos nombre y código prellenados
- [ ] Toast "Datos del escáner cargados"

4. Completar, guardar, volver a Compras y escanear

**Verificar:**
- [ ] Ahora SÍ lo encuentra

---

### ESCENARIO 3: Prevención de duplicados

1. Abrir: `http://localhost:8000/app-beta-2024/producto/crear/`
2. Escanear un producto que YA EXISTE

**Verificar:**
- [ ] Aparece "Producto ya registrado"
- [ ] Muestra nombre y stock
- [ ] Botón "Ir a Crear Compra"

3. Clic en "Ir a Crear Compra"

**Verificar:**
- [ ] Redirige correctamente

---

## Problemas comunes

| Problema | Solución |
|----------|----------|
| Error 500 - GOOGLE_VISION_API_KEY | Verificar en `core/settings.py` que la key esté configurada |
| La cámara no se activa | Usar HTTPS o localhost; revisar permisos del navegador |
| TypeError: NoneType | Ejecutar `python verificar_modelo.py` y agregar campos faltantes |
| productos.length is undefined | Usar `data.productos \|\| data.products \|\| []` |
| Formulario no se rellena | Verificar IDs: `#id_producto`, `#id_nombre`, `#id_codigo_barras` |

---

## Checklist final

**Backend:**
- [ ] API responde a POST
- [ ] Respuesta incluye `productos` y `products`
- [ ] Campo `contexto` en meta es correcto
- [ ] Búsqueda encuentra por nombre y código

**Crear Producto:**
- [ ] Botón de escáner visible
- [ ] Modal se abre, cámara activa
- [ ] Prellenado funciona (producto nuevo)
- [ ] Advertencia funciona (producto existente)

**Crear Compra:**
- [ ] Escáner encuentra productos
- [ ] Rellena formulario
- [ ] Redirección funciona (producto no existe)
- [ ] Stock se actualiza al guardar

**Crear Venta:**
- [ ] Escáner agrega al carrito
- [ ] Usa precio PVP
- [ ] Stock disminuye al finalizar

**Ciclo completo:**
- [ ] Producto -> Compra -> Venta funciona
- [ ] Sin errores en consola

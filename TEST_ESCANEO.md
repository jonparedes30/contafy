# 🧪 PRUEBA DEL FLUJO DE ESCANEO (CON 4 FIXES)

## ¿QUÉ CAMBIÓ?

- ✅ FIX 1: Frontend envía `nombre` y `marca` al backend
- ✅ FIX 2: Backend busca en TODOS los OCR/logos (no solo primeros 3/2)
- ✅ FIX 2: Aumentó límite de resultados de 15/10 a 50
- ✅ FIX 3: Acepta barcodes 6+ dígitos  
- ✅ FIX 4: Usa OCR/logos como fallback si no viene nombre/marca

## PASOS PARA PROBAR

### 1. Crea productos de prueba (si no existen)
Voy a **Inventario > Listar Productos**
- Agrega algunos productos con nombres como:
  - "Coca Cola"
  - "Sprite"
  - "Fanta"

### 2. Vai a **Crear Venta**
- Verás campo: `🔍 Escanea o escribe código o producto`
- Botón: `[Escanear]`

### 3. Hace clic en "Escanear"
- Se abre modal con cámara
- 📸 Captura una imagen de un producto

### 4. Vision detecta
- Muestra logos, etiquetas, texto OCR
- Botón: `[Autorrellenar formulario]`

### 5. Hace clic en "Autorrellenar"
- **AHORA** (con FIX 1) se envían:
  - `{detection: {...}, nombre: "...", marca: "..."}`
  
- Backend busca (con FIX 2):
  - ✅ Barcode exacto
  - ✅ TODOS los OCR texts (antes era max 3)
  - ✅ TODOS los logos (antes era max 2)
  - ✅ Nombre/marca que detectó
  - ✅ Hasta 50 results por categoría (antes 15/10)

### 6. Respuesta del endpoint

**Si encontró:**
```
┌─────────────────────────────┐
│ Coca Cola encontrado ✅    │
├─────────────────────────────┤
│ - Coca Cola              │
│   Stock: 100             │
│   Precio: $2.50          │
│            [Usar]        │
└─────────────────────────────┘
```

→ Usuario hace clic en `[Usar]`
→ **Se agrega automáticamente al carrito**
→ Tabla de venta ahora muestra:
```
PRODUCTO     CANT. P.UNIT SUBTOTAL ACCIÓN
Coca Cola 1  1     $2.50  $2.50    [✕]
```

**Si no encontró:**
```
Producto no encontrado - Rellenando formulario...
```
→ Los campos se prellenan:
```
Nombre: Coca Cola
Marca: (detectada)
Código barras: (si se extrajo)
```
→ Usuario completa y guarda

## DIAGNÓSTICO SI NO FUNCIONA

Si **aún no encuentra** los productos:

Abre **Consola del navegador** (F12):
1. Pestaña "Console"
2. Mira si hay errores JavaScript
3. Pestaña "Network"
4. Busca POST a `/app-beta-2024/producto/prefill_from_scan/`
5. Ve la respuesta del servidor

Si ves `"found": false` cuando debería ser `true`:
- Verifica que el producto existe en Inventario
- Revisa que esté en la misma empresa
- Prueba con nombre exacto (sin tildes)

## CAMBIOS DE CÓDIGO

### Frontend  
`empresa/static/js/vision_scanner.js`:
- Línea 133-145: Extrae `nombre` y `marca` de detection
- Línea 149: Cambia regex barcode a 6+ dígitos
- Línea 166: Envía `{detection, nombre, marca}`

### Backend
`empresa/views/productos.py`:
- Línea 425: `ocr_texts[3:]` → `ocr_texts` (busca TODO)
- Línea 429: `[:15]` → `[:50]` (más resultados)
- Línea 442: `logos[:2]` → `logos` (busca TODO) 
- Línea 446: `[:10]` → `[:50]` (más resultados)
- Línea 460-464: Fallback a OCR/logo si no hay nombre/marca
- Línea 470: `[:10]` → `[:50]`


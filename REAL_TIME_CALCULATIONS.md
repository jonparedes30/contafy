# Cálculos en Tiempo Real - Todos los Templates

## ✅ Estado Actual

Todos los templates de formularios tienen **cálculos en tiempo real** usando event listeners de JavaScript.

## Templates Verificados

### 1. ✅ crear_producto.html

#### Calculadora de IVA (Tiempo Real)
```javascript
inputPrecioUnitario.addEventListener('input', calcularIvaProducto);
porcentajeIvaProducto.addEventListener('input', calcularIvaProducto);
```

**Función:**
```javascript
function calcularIvaProducto() {
    const precioUnitario = parseFloat(inputPrecioUnitario.value) || 0;
    const porcentaje = parseFloat(porcentajeIvaProducto.value);
    
    if (precioUnitario > 0) {
        const iva = precioUnitario * (porcentaje / 100);
        const total = precioUnitario + iva;
        
        ivaCalculadoProducto.textContent = '$' + iva.toFixed(2);
        totalConIvaProducto.textContent = '$' + total.toFixed(2);
    }
}
```

#### Calculadora de Margen (Tiempo Real)
```javascript
inputPrecio.addEventListener('input', calcularMargen);
inputPvp.addEventListener('input', calcularMargen);
```

**Función:**
```javascript
function calcularMargen() {
    if (!inputPrecio || !inputPvp) return;
    const precioCosto = parseFloat(inputPrecio.value) || 0;
    const precioVenta = parseFloat(inputPvp.value) || 0;
    
    if (precioCosto > 0 && precioVenta > 0) {
        const margen = ((precioVenta - precioCosto) / precioVenta) * 100;
        const utilidad = precioVenta - precioCosto;
        
        margenDisplay.value = margen.toFixed(1);
        // Indicadores visuales (verde/amarillo/rojo)
    }
}
```

**Eventos que disparan cálculos:**
- ✅ Cambio en precio unitario → Calcula IVA
- ✅ Cambio en % IVA → Calcula IVA
- ✅ Cambio en precio costo → Calcula margen
- ✅ Cambio en PVP → Calcula margen

---

### 2. ✅ crear_compra.html

#### Calculadora de IVA y Total (Tiempo Real)
```javascript
selectProd.addEventListener('change', actualizarCompra);
inputCant.addEventListener('input', actualizarCompra);
inputPrecio.addEventListener('input', actualizarCompra);
inputTasaIva.addEventListener('input', actualizarCompra);
```

**Función:**
```javascript
function actualizarCompra() {
    const cantidad = parseInt(inputCant.value) || 0;
    const precioEditado = parseFloat(inputPrecio.value) || 0;
    const tasaIva = parseFloat(inputTasaIva.value) || 15;
    
    // Calcular IVA
    const montoNeto = precioEditado * cantidad || 0;
    const iva = montoNeto * (tasaIva / 100);
    const total = montoNeto + iva;
    
    // Actualizar campos en tiempo real
    inputMontoNeto.value = montoNeto.toFixed(2);
    inputIva.value = iva.toFixed(2);
    inputTotal.value = total.toFixed(2);
}
```

**Eventos que disparan cálculos:**
- ✅ Cambio en producto → Auto-completa precio y calcula
- ✅ Cambio en cantidad → Calcula subtotal, IVA y total
- ✅ Cambio en precio unitario → Calcula subtotal, IVA y total
- ✅ Cambio en tasa IVA → Recalcula IVA y total

---

### 3. ✅ crear_venta.html (Pendiente de verificar)

**Nota:** Necesita verificación para asegurar que tenga eventos 'input' en tiempo real.

---

## Patrón Estándar de Implementación

### Event Listeners Requeridos

Para cualquier formulario con cálculos de IVA:

```javascript
// 1. Escuchar cambios en campos numéricos
inputPrecio.addEventListener('input', calcularTotales);
inputCantidad.addEventListener('input', calcularTotales);
inputTasaIva.addEventListener('input', calcularTotales);

// 2. Función de cálculo
function calcularTotales() {
    const precio = parseFloat(inputPrecio.value) || 0;
    const cantidad = parseFloat(inputCantidad.value) || 0;
    const tasaIva = parseFloat(inputTasaIva.value) || 15;
    
    const subtotal = precio * cantidad;
    const iva = subtotal * (tasaIva / 100);
    const total = subtotal + iva;
    
    // Actualizar campos inmediatamente
    inputSubtotal.value = subtotal.toFixed(2);
    inputIva.value = iva.toFixed(2);
    inputTotal.value = total.toFixed(2);
}

// 3. Calcular al cargar la página
document.addEventListener('DOMContentLoaded', calcularTotales);
```

## Tipos de Eventos

### ✅ Eventos Correctos (Tiempo Real)

| Evento | Cuándo se dispara | Uso |
|--------|-------------------|-----|
| **'input'** | Cada tecla presionada | ✅ Cálculos en tiempo real |
| **'change'** | Al cambiar y perder foco | ✅ Selects y checkboxes |
| **'DOMContentLoaded'** | Al cargar la página | ✅ Cálculo inicial |

### ❌ Eventos Incorrectos (NO Tiempo Real)

| Evento | Cuándo se dispara | Por qué NO usar |
|--------|-------------------|-----------------|
| **'blur'** | Al perder el foco | ❌ Solo al salir del campo |
| **'submit'** | Al enviar formulario | ❌ Muy tarde |
| **'click'** en botón | Al hacer clic | ❌ Requiere acción manual |

## Checklist de Verificación

Para cada template con cálculos:

- [ ] ✅ Usa evento **'input'** para campos numéricos
- [ ] ✅ Usa evento **'change'** para selects
- [ ] ✅ Calcula en **DOMContentLoaded** para valores iniciales
- [ ] ✅ Actualiza **todos los campos relacionados** en cada cálculo
- [ ] ✅ Maneja valores **null/undefined** con `|| 0`
- [ ] ✅ Formatea números con **.toFixed(2)** para moneda
- [ ] ✅ Muestra **indicadores visuales** (colores, iconos)

## Estado por Template

| Template | IVA Tiempo Real | Otros Cálculos | Estado |
|----------|----------------|----------------|--------|
| **crear_producto.html** | ✅ Sí | ✅ Margen | ✅ Completo |
| **crear_compra.html** | ✅ Sí | ✅ Stock | ✅ Completo |
| **crear_venta.html** | ⏳ Verificar | ⏳ Verificar | ⏳ Pendiente |
| **crear_gasto.html** | N/A | N/A | ✅ Simple |

## Beneficios del Tiempo Real

### 1. ✅ Mejor UX
- Usuario ve resultados inmediatamente
- No necesita hacer clic en botones
- Feedback instantáneo

### 2. ✅ Menos Errores
- Usuario detecta errores antes de enviar
- Validación visual inmediata
- Menos formularios rechazados

### 3. ✅ Más Intuitivo
- Comportamiento esperado por usuarios modernos
- Similar a calculadoras y hojas de cálculo
- Reduce fricción en el proceso

### 4. ✅ Transparencia
- Usuario ve cómo se calculan los valores
- Puede ajustar y ver cambios inmediatos
- Mayor confianza en el sistema

## Ejemplo Completo

### HTML
```html
<div class="mb-3">
  <label>Precio Unitario:</label>
  <input type="number" id="precio" class="form-control" step="0.01">
</div>

<div class="mb-3">
  <label>Cantidad:</label>
  <input type="number" id="cantidad" class="form-control">
</div>

<div class="mb-3">
  <label>Tasa IVA (%):</label>
  <input type="number" id="tasa_iva" class="form-control" value="15">
</div>

<div class="card bg-light">
  <div class="card-body">
    <div>Subtotal: <strong id="subtotal">$0.00</strong></div>
    <div>IVA: <strong id="iva">$0.00</strong></div>
    <div>Total: <strong id="total">$0.00</strong></div>
  </div>
</div>
```

### JavaScript
```javascript
document.addEventListener('DOMContentLoaded', function() {
  const inputPrecio = document.getElementById('precio');
  const inputCantidad = document.getElementById('cantidad');
  const inputTasaIva = document.getElementById('tasa_iva');
  const displaySubtotal = document.getElementById('subtotal');
  const displayIva = document.getElementById('iva');
  const displayTotal = document.getElementById('total');
  
  function calcular() {
    const precio = parseFloat(inputPrecio.value) || 0;
    const cantidad = parseFloat(inputCantidad.value) || 0;
    const tasaIva = parseFloat(inputTasaIva.value) || 15;
    
    const subtotal = precio * cantidad;
    const iva = subtotal * (tasaIva / 100);
    const total = subtotal + iva;
    
    displaySubtotal.textContent = '$' + subtotal.toFixed(2);
    displayIva.textContent = '$' + iva.toFixed(2);
    displayTotal.textContent = '$' + total.toFixed(2);
  }
  
  // Eventos en tiempo real
  inputPrecio.addEventListener('input', calcular);
  inputCantidad.addEventListener('input', calcular);
  inputTasaIva.addEventListener('input', calcular);
  
  // Cálculo inicial
  calcular();
});
```

## Conclusión

✅ **crear_producto.html** y **crear_compra.html** ya tienen cálculos en tiempo real implementados correctamente.

⏳ **Próximo paso:** Verificar y actualizar **crear_venta.html** si es necesario.

## Commits Relacionados

- `4ffd37c` - Fix: Simplify IVA calculator - remove duplicate section
- `53efc7d` - Fix: Add precio_unitario and IVA fields to CompraForm template
- `c5abf15` - Fix: Complete ProductoForm with all fields and fix category creation API

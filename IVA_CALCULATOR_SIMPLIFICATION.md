# Simplificación Calculadora IVA - Template Compra

## Problema
El template de crear compra tenía **DOS secciones de IVA duplicadas**:

### ❌ Antes (Duplicado)

**Sección 1: "🧮 Cálculo de IVA"**
- % IVA (input manual)
- IVA a pagar (display)
- Total que pagarás (display)

**Sección 2: "💰 Detalles del IVA"**
- Monto Neto (input readonly)
- Tasa IVA (%) (input)
- IVA (input readonly)
- Total (input readonly)

**Problema:** Confusión para el usuario, código duplicado, dos lugares para configurar el IVA.

## Solución Aplicada

### ✅ Después (Unificado)

**Sección Única: "💰 Cálculo de IVA"**

| Campo | Tipo | Descripción | Editable |
|-------|------|-------------|----------|
| **Subtotal (sin IVA)** | Number | Precio × Cantidad | ❌ No (auto) |
| **Tasa IVA (%)** | Number | Porcentaje de IVA | ✅ Sí |
| **IVA a pagar** | Number | Subtotal × (Tasa / 100) | ❌ No (auto) |
| **Total a pagar** | Number | Subtotal + IVA | ❌ No (auto) |

## Estructura del Template

```html
<!-- Precio Unitario -->
<div class="mb-3">
  {{ form.precio_unitario.label_tag }}
  {{ form.precio_unitario }}
  <div class="form-text">Precio de compra por unidad (sin IVA)</div>
</div>

<!-- Cálculo Automático de IVA -->
<div class="mb-3">
  <div class="card bg-light">
    <div class="card-body">
      <h6 class="text-primary mb-3">💰 Cálculo de IVA</h6>
      
      <div class="row mb-3">
        <!-- Subtotal -->
        <div class="col-md-6">
          <label>Subtotal (sin IVA):</label>
          {{ form.monto_neto }}
          <div class="form-text">Precio × Cantidad</div>
        </div>
        
        <!-- Tasa IVA -->
        <div class="col-md-6">
          <label>Tasa IVA (%):</label>
          {{ form.tasa_iva }}
          <div class="form-text">Default: 15%</div>
        </div>
      </div>
      
      <div class="row">
        <!-- IVA -->
        <div class="col-md-6">
          <label>IVA a pagar:</label>
          {{ form.iva }}
          <div class="form-text">Subtotal × (Tasa / 100)</div>
        </div>
        
        <!-- Total -->
        <div class="col-md-6">
          <label><strong>Total a pagar:</strong></label>
          <input type="number" name="monto" readonly>
          <div class="form-text"><strong>Subtotal + IVA</strong></div>
        </div>
      </div>
    </div>
  </div>
</div>
```

## JavaScript Simplificado

### ❌ Antes (Duplicado)
```javascript
// Calculadora 1
function calcularIvaCompra() {
  const precioUnitario = parseFloat(inputPrecioUnitario.value) || 0;
  const porcentaje = parseFloat(porcentajeIva.value);
  const iva = precioUnitario * (porcentaje / 100);
  const total = precioUnitario + iva;
  ivaCalculadoCompra.textContent = '$' + iva.toFixed(2);
  totalConIvaCompra.textContent = '$' + total.toFixed(2);
}

// Calculadora 2
function actualizarCompra() {
  const montoNeto = precioEditado * cantidad || 0;
  const iva = montoNeto * (tasaIva / 100);
  const total = montoNeto + iva;
  inputMontoNeto.value = montoNeto.toFixed(2);
  inputIva.value = iva.toFixed(2);
  inputTotal.value = total.toFixed(2);
}
```

### ✅ Después (Unificado)
```javascript
function actualizarCompra() {
  const cantidad = parseInt(inputCant.value) || 0;
  const precioEditado = parseFloat(inputPrecio.value) || 0;
  const tasaIva = parseFloat(inputTasaIva.value) || 15;
  
  // Calcular IVA
  const montoNeto = precioEditado * cantidad || 0;
  const iva = montoNeto * (tasaIva / 100);
  const total = montoNeto + iva;
  
  // Actualizar campos
  inputMontoNeto.value = montoNeto.toFixed(2);
  inputIva.value = iva.toFixed(2);
  inputTotal.value = total.toFixed(2);
}

// Event listeners
selectProd.addEventListener('change', actualizarCompra);
inputCant.addEventListener('input', actualizarCompra);
inputPrecio.addEventListener('input', actualizarCompra);
inputTasaIva.addEventListener('input', actualizarCompra);
```

## Funcionalidad Clara

### Flujo de Cálculo

1. Usuario selecciona **Producto** → Auto-completa precio unitario
2. Usuario ingresa **Cantidad** → Calcula subtotal
3. Sistema calcula automáticamente:
   - **Subtotal** = Precio × Cantidad
   - **IVA** = Subtotal × (Tasa / 100)
   - **Total** = Subtotal + IVA
4. Usuario puede ajustar **Tasa IVA** si es diferente de 15%
5. Todos los campos se recalculan en tiempo real

### Campos Editables vs Auto-calculados

| Campo | Usuario puede editar | Se calcula automáticamente |
|-------|---------------------|---------------------------|
| Precio Unitario | ✅ Sí | Desde producto |
| Cantidad | ✅ Sí | - |
| Subtotal | ❌ No | ✅ Precio × Cantidad |
| Tasa IVA | ✅ Sí | Default 15% |
| IVA | ❌ No | ✅ Subtotal × Tasa |
| Total | ❌ No | ✅ Subtotal + IVA |

## Beneficios de la Simplificación

### 1. ✅ Claridad
- Una sola sección de IVA
- Flujo lógico de arriba a abajo
- Etiquetas descriptivas con fórmulas

### 2. ✅ Menos Código
- **85 líneas eliminadas**
- JavaScript más simple
- Menos mantenimiento

### 3. ✅ Mejor UX
- No hay confusión sobre dónde configurar el IVA
- Todos los cálculos en un solo lugar
- Textos de ayuda claros

### 4. ✅ Consistencia
- Mismo patrón que otros formularios
- Fórmulas visibles para el usuario
- Validación más simple

## Comparación con ProductoForm

| Característica | ProductoForm | CompraForm |
|----------------|--------------|------------|
| **Calculadora IVA** | Simple (informativa) | Completa (con campos) |
| **Campos IVA** | Solo display | Inputs editables |
| **Propósito** | Mostrar IVA de venta | Calcular IVA de compra |
| **Complejidad** | Baja | Media |

## Commit

**Commit:** `4ffd37c` - Fix: Simplify IVA calculator - remove duplicate section

**Cambios:**
- ❌ Eliminada sección duplicada "🧮 Cálculo de IVA"
- ✅ Unificada en "💰 Cálculo de IVA"
- ❌ Eliminado JavaScript duplicado
- ✅ Simplificado a una sola función
- 📉 **85 líneas de código eliminadas**

## Testing

### Verificar que funciona:
1. ✅ Ir a `/app-beta-2024/compra/crear/`
2. ✅ Ver UNA sola sección de IVA
3. ✅ Seleccionar producto → precio se auto-completa
4. ✅ Ingresar cantidad → subtotal se calcula
5. ✅ Ver IVA calculado automáticamente
6. ✅ Ver total calculado automáticamente
7. ✅ Cambiar tasa IVA → todo se recalcula
8. ✅ Crear compra → se guarda correctamente

## Próximos Pasos

Esperar ~5 minutos para que Render despliegue el commit `4ffd37c` y verificar que:
1. Solo hay una sección de IVA
2. Todos los cálculos funcionan correctamente
3. La interfaz es más clara y simple
4. No hay errores de JavaScript

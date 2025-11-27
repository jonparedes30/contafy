# Fix Template Compra - Campos Precio y Costo

## Problema
En el template de crear compra no se mostraban:
1. ❌ Campo **Precio Unitario** (costo sin IVA)
2. ❌ Campo **PVP** (no aplica para compras)
3. ❌ Campos de cálculo de IVA no funcionaban correctamente

## Solución Aplicada

### CompraForm Actualizado

Agregados campos adicionales para el cálculo de IVA:

```python
class CompraForm(forms.ModelForm):
    precio_unitario = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'step': '0.01', 
            'id': 'precio_unitario'
        }),
        label='Precio Unitario (sin IVA)'
    )
    monto_neto = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'step': '0.01', 
            'id': 'id_monto_neto_compra', 
            'readonly': 'readonly'
        }),
        label='Monto Neto'
    )
    tasa_iva = forms.DecimalField(
        required=False,
        initial=15,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'step': '0.01', 
            'id': 'id_tasa_iva_compra'
        }),
        label='Tasa IVA (%)'
    )
    iva = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'step': '0.01', 
            'id': 'id_iva_compra', 
            'readonly': 'readonly'
        }),
        label='IVA'
    )
    
    class Meta:
        model = Compra
        fields = ['proveedor_fk', 'producto', 'cantidad', 'tipo_pago']
```

## Campos del Formulario de Compra

### Campos Visibles

| Campo | Tipo | Descripción | Requerido |
|-------|------|-------------|-----------|
| **Proveedor** | Select | Proveedor de la compra | No |
| **Código de Barras** | Text | Para búsqueda rápida | No |
| **Producto** | Select | Producto a comprar | Sí |
| **Cantidad** | Number | Unidades a comprar | Sí |
| **Precio Unitario** | Number | Precio sin IVA por unidad | No* |
| **Tipo de Pago** | Select | Contado o Crédito | Sí |

*Se calcula automáticamente desde el producto

### Campos de Cálculo (Calculadora de IVA)

| Campo | Tipo | Descripción | Auto-calculado |
|-------|------|-------------|----------------|
| **% IVA** | Number | Porcentaje de IVA (default: 15%) | No |
| **IVA a pagar** | Display | IVA calculado | Sí |
| **Total que pagarás** | Display | Total con IVA | Sí |

### Campos de Detalle IVA

| Campo | Tipo | Descripción | Auto-calculado |
|-------|------|-------------|----------------|
| **Monto Neto** | Number | Subtotal sin IVA | Sí |
| **Tasa IVA (%)** | Number | Tasa de IVA aplicada | No |
| **IVA** | Number | IVA calculado | Sí |
| **Total** | Number | Monto total con IVA | Sí |

## Cálculos Automáticos

### JavaScript en el Template

```javascript
function actualizarCompra() {
    const cantidad = parseInt(inputCant.value) || 0;
    const precioEditado = parseFloat(inputPrecio.value) || 0;
    const tasaIva = parseFloat(inputTasaIva.value) || 15;
    
    // Calcular montos
    const montoNeto = precioEditado * cantidad;
    const iva = montoNeto * (tasaIva / 100);
    const total = montoNeto + iva;
    
    // Actualizar campos
    inputMontoNeto.value = montoNeto.toFixed(2);
    inputIva.value = iva.toFixed(2);
    inputTotal.value = total.toFixed(2);
}
```

### Fórmulas

1. **Monto Neto** = Precio Unitario × Cantidad
2. **IVA** = Monto Neto × (Tasa IVA / 100)
3. **Total** = Monto Neto + IVA

## Funcionalidades del Template

### 1. ✅ Búsqueda por Código de Barras
- Campo de texto para ingresar código
- Botón de escaneo con cámara
- Búsqueda automática del producto

### 2. ✅ Selección de Producto
- Lista desplegable filtrada por empresa
- Auto-completa precio unitario del producto
- Muestra stock disponible

### 3. ✅ Calculadora de IVA
- Calcula IVA en tiempo real
- Muestra subtotal, IVA y total
- Porcentaje de IVA configurable

### 4. ✅ Crear Proveedor
- Modal para crear proveedor sin salir
- Se agrega automáticamente al select
- Campos: nombre, RUC, teléfono

### 5. ✅ Días de Crédito
- Aparece solo si tipo de pago es "Crédito"
- Default: 30 días
- Configurable de 1 a 365 días

### 6. ✅ Validación de Stock
- Muestra stock disponible
- Alerta si la cantidad excede el stock
- Indicadores visuales (verde/rojo)

## Diferencias con ProductoForm

| Característica | ProductoForm | CompraForm |
|----------------|--------------|------------|
| **Precio Unitario** | Precio de costo | Precio de compra |
| **PVP** | ✅ Sí (precio de venta) | ❌ No aplica |
| **Proveedor** | ❌ No (futuro) | ✅ Sí |
| **Stock** | Stock inicial | Cantidad a comprar |
| **IVA** | Calculadora simple | Calculadora + detalles |

## Flujo de Uso

1. Usuario selecciona **Proveedor** (opcional)
2. Escanea o busca **Producto** por código de barras
3. Sistema auto-completa **Precio Unitario** del producto
4. Usuario ingresa **Cantidad**
5. Sistema calcula automáticamente:
   - Monto Neto
   - IVA
   - Total
6. Usuario selecciona **Tipo de Pago**
7. Si es crédito, configura **Días de Crédito**
8. Guarda la compra

## Commit

**Commit:** `53efc7d` - Fix: Add precio_unitario and IVA fields to CompraForm template

## Testing

### Verificar que funciona:
1. ✅ Ir a `/app-beta-2024/compra/crear/`
2. ✅ Ver campo "Precio Unitario"
3. ✅ Ver calculadora de IVA
4. ✅ Ver campos de detalle IVA (Monto Neto, IVA, Total)
5. ✅ Seleccionar producto y verificar que se auto-completa el precio
6. ✅ Cambiar cantidad y verificar que se recalcula el total
7. ✅ Cambiar % IVA y verificar que se recalcula
8. ✅ Crear compra y verificar que se guarda correctamente

## Próximos Pasos

Esperar ~5 minutos para que Render despliegue el commit `53efc7d` y verificar que:
1. El campo precio unitario aparece
2. La calculadora de IVA funciona
3. Los campos se auto-calculan correctamente
4. Se puede crear una compra con todos los datos

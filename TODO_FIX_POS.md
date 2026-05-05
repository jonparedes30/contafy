# ✅ COMPLETADO: Correcciones POS - IVA, Cambio y Lógica Contable

## Problemas corregidos:
1. ✅ IVA ahora se muestra correctamente en el panel POS
2. ✅ Cálculo del cambio funciona correctamente
3. ✅ Lógica contable completa al cobrar (asientos, movimientos, costos)

## Archivos modificados:
- [x] `empresa/templates/empresa/crear_venta.html` - Fix JS de cálculos
- [x] `empresa/views/ventas.py` - Fix lógica contable en `crear_venta_multiple()`

## Cambios aplicados:

### 1. Fix crear_venta.html ✅
- [x] Corregir `calcularTotalMultiple()` para pasar IVA a `POSQuickBox.updateCartTotals()`
- [x] Agregar llamada a `updatePosChange()` después de calcular totales
- [x] Asegurar sincronización del input de monto recibido
- [x] Fix: Manejar caso cuando `checkboxIva` es null (modo POS oculta UI legacy)
- [x] Fix: `updatePosChange()` ahora obtiene total desde input o display como fallback

### 2. Fix ventas.py ✅
- [x] Agregar `venta.crear_asientos_contables()` en `crear_venta_multiple()`
- [x] Agregar movimientos contables según tipo de pago (contado, transferencia, tarjeta, crédito)
- [x] Agregar registro de costo de ventas (manufactura/comercio vs servicios)
- [x] Crear cuenta por cobrar si el tipo de pago es 'credito'
- [x] Calcular costo unitario según categoría de empresa

## Resumen de funcionalidad:
- IVA se calcula y muestra correctamente en tiempo real
- Cambio se recalcula automáticamente al modificar productos o monto recibido
- Al cobrar, se ejecuta la lógica contable completa:
  - Asientos contables por cada venta
  - Movimientos contables (Caja/Banco → Ventas)
  - Registro de costo de ventas (Costo de Ventas → Inventario/Caja)
  - Cuentas por cobrar para ventas a crédito
  - Descuento de stock del inventario

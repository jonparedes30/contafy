# 📋 PLAN DE IMPLEMENTACIÓN POR PARTES

**Objetivo:** Completar auditoría y validar sistema completo
**Estrategia:** Dividir en partes pequeñas y ejecutables

---

## PARTE 1: CREAR TEMPLATES POR CATEGORÍA (2-3 horas)

### 1.1 Dashboard por Categoría
- [ ] `empresa/comercio/dashboard.html`
- [ ] `empresa/manufactura/dashboard.html`
- [ ] `empresa/servicio/dashboard.html`

### 1.2 Resumen por Categoría
- [ ] `empresa/comercio/resumen.html`
- [ ] `empresa/manufactura/resumen.html`
- [ ] `empresa/servicio/resumen.html`

### 1.3 Crear Venta por Categoría
- [ ] `empresa/comercio/crear_venta.html`
- [ ] `empresa/manufactura/crear_venta.html`
- [ ] `empresa/servicio/crear_venta.html`

---

## PARTE 2: APLICAR PRESENTERS EN VISTAS (2-3 horas)

### 2.1 Dashboard
- [ ] Modificar `views/dashboard.py`
- [ ] Usar `DashboardPresenter`
- [ ] Selección dinámica de template

### 2.2 Ventas
- [ ] Crear `VentasPresenter`
- [ ] Modificar `views/ventas.py`
- [ ] Normalizar variables

### 2.3 Gastos
- [ ] Crear `GastosPresenter`
- [ ] Modificar `views/gastos.py`
- [ ] Normalizar variables

---

## PARTE 3: VALIDAR FLUJOS CRÍTICOS (1-2 horas)

### 3.1 Flujo de Venta
- [ ] Test: Crear venta al contado
- [ ] Verificar: Asientos contables creados
- [ ] Verificar: Stock actualizado
- [ ] Verificar: IVA calculado correctamente

### 3.2 Flujo de Venta a Crédito
- [ ] Test: Crear venta a crédito
- [ ] Verificar: Cuenta por cobrar creada
- [ ] Verificar: Cliente creado si no existe
- [ ] Verificar: Asientos correctos

### 3.3 Flujo de Compra
- [ ] Test: Crear compra
- [ ] Verificar: Asientos contables
- [ ] Verificar: Stock actualizado
- [ ] Verificar: IVA registrado

---

## PARTE 4: CORREGIR PROBLEMAS DETECTADOS (1-2 horas)

### 4.1 Habilitar Asientos de Capital
- [ ] Descomentar `crear_asientos_contables()` en Capital
- [ ] Validar que no cause bucle
- [ ] Test: Crear aporte
- [ ] Test: Crear retiro

### 4.2 Validar Límites de Crédito
- [ ] Agregar validación en Venta.save()
- [ ] Verificar límite antes de crear CxC
- [ ] Mostrar error si excede límite

---

## PARTE 5: REFACTORIZAR CON COMPONENTES (2-3 horas)

### 5.1 Refactorizar Listados
- [ ] `listar_ventas.html` → usar `_table.html`
- [ ] `listar_gastos.html` → usar `_table.html`
- [ ] `listar_productos.html` → usar `_table.html`

### 5.2 Refactorizar Alertas
- [ ] `resumen.html` → usar `_alertas.html`
- [ ] `dashboard.html` → usar `_alertas.html`

---

## PARTE 6: TESTS Y VALIDACIÓN (2-3 horas)

### 6.1 Tests de Presenters
- [ ] Test: ResumenPresenter
- [ ] Test: DashboardPresenter
- [ ] Test: VentasPresenter

### 6.2 Tests de Componentes
- [ ] Test: _table.html renderiza
- [ ] Test: _alertas.html renderiza
- [ ] Test: _kpi_card.html renderiza

---

## ESTIMACIÓN TOTAL: 10-16 horas

**Prioridad de ejecución:**
1. PARTE 1 (Templates) - Base para todo
2. PARTE 2 (Presenters) - Normalización
3. PARTE 3 (Validación) - Asegurar funcionalidad
4. PARTE 4 (Correcciones) - Bugs críticos
5. PARTE 5 (Refactorización) - Mejora de código
6. PARTE 6 (Tests) - Calidad

---

## ¿POR DÓNDE EMPEZAR?

**Opción A:** PARTE 1 completa (Templates por categoría)
**Opción B:** PARTE 3 primero (Validar que todo funciona)
**Opción C:** PARTE 4 primero (Corregir bugs críticos)


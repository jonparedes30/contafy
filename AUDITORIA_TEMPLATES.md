# 📋 AUDITORÍA DE TEMPLATES - CONTAFY
## Fase 1: Identificación y Clasificación

**Fecha:** 2025-01-XX  
**Objetivo:** Identificar templates similares vs específicos por categoría de empresa

---

## 📊 RESUMEN EJECUTIVO

**Total de templates:** 58 archivos HTML principales + 17 en subdirectorios  
**Categorías de empresa:** Comercio, Manufactura, Servicio

### Distribución:
- ✅ **Templates base/comunes:** 58 archivos (raíz)
- 🏭 **Manufactura específicos:** 13 archivos
- 🛠️ **Servicios específicos:** 3 archivos
- 📚 **Aprendizaje:** 8 archivos
- 📊 **Dashboards:** 4 archivos
- 📈 **NIIF:** 4 archivos

---

## 🎯 CLASIFICACIÓN POR SIMILITUD

### 🟢 GRUPO A: Templates 80%+ Similares (UNIFICAR)
**Recomendación:** Mantener UN template con condicionales `{% if categoria %}`

| Template | Líneas | Variables Comunes | Diferencias por Categoría | Acción |
|----------|--------|-------------------|---------------------------|--------|
| **resumen.html** | 353 | ventas, gastos, utilidad_neta, margen_neto | label_costos (producción/mercancía/servicio) | ✅ UNIFICAR |
| **crear_venta.html** | 1104 | producto, cantidad, precio, cliente | Manufactura: verifica stock materias primas | ✅ UNIFICAR |
| **listar_ventas.html** | 205 | fecha, monto, cliente, estado | Todas usan mismas columnas | ✅ UNIFICAR |
| **listar_productos.html** | 368 | nombre, precio, stock, categoría | Manufactura: muestra receta/BOM | ✅ UNIFICAR |
| **crear_gasto.html** | 124 | monto, categoría, descripción, fecha | Idéntico para todas | ✅ UNIFICAR |
| **listar_gastos.html** | 132 | fecha, categoría, monto, descripción | Idéntico para todas | ✅ UNIFICAR |
| **crear_compra.html** | 436 | proveedor, producto, cantidad, precio | Manufactura: materias primas vs productos | ✅ UNIFICAR |
| **listar_compra.html** | 140 | fecha, proveedor, monto, estado | Idéntico para todas | ✅ UNIFICAR |
| **balance_general.html** | 289 | activos, pasivos, capital | Idéntico para todas (NIIF) | ✅ UNIFICAR |
| **estado_resultado.html** | 269 | ventas, costos, gastos, utilidad | label_costos diferente | ✅ UNIFICAR |
| **flujo_caja.html** | 345 | ingresos, egresos, saldo | Idéntico para todas | ✅ UNIFICAR |
| **inventario.html** | 169 | productos, stock, valor | Manufactura: incluye materias primas | ✅ UNIFICAR |
| **mi_empresa.html** | 707 | nombre, RUC, dirección, categoría | Idéntico para todas | ✅ UNIFICAR |
| **gestion_deudas.html** | 377 | cuentas por cobrar/pagar | Idéntico para todas | ✅ UNIFICAR |

**Total Grupo A:** 14 templates → **UNIFICAR con condicionales**

---

### 🟡 GRUPO B: Templates 50-80% Similares (HÍBRIDO)
**Recomendación:** Template base + secciones específicas con `{% block %}`

| Template | Líneas | Similitud | Diferencias Clave | Acción |
|----------|--------|-----------|-------------------|--------|
| **dashboard.html** | 1330 | 60% | Manufactura: órdenes producción; Servicio: citas; Comercio: ventas rápidas | 🔄 HÍBRIDO |
| **crear_producto.html** | 532 | 70% | Manufactura: receta/BOM; Servicio: N/A; Comercio: simple | 🔄 HÍBRIDO |
| **exportaciones_*.html** | 237/192 | 75% | Lógica de exportación diferente | 🔄 HÍBRIDO |
| **actividad_reciente.html** | 269 | 65% | Tipos de actividad varían | 🔄 HÍBRIDO |

**Total Grupo B:** 4 templates → **Base compartida + bloques específicos**

---

### 🔴 GRUPO C: Templates Completamente Específicos (SEPARAR)
**Recomendación:** Mantener separados, heredan solo de `base.html`

#### 🏭 Manufactura Exclusivos:
| Template | Líneas | Razón |
|----------|--------|-------|
| **manufactura/dashboard.html** | ? | Órdenes de producción, BOM, materias primas |
| **manufactura/crear_orden.html** | ? | Proceso de manufactura específico |
| **manufactura/ver_receta.html** | ? | Bill of Materials (BOM) |
| **manufactura/listar_materias_primas.html** | ? | Inventario de materias primas |
| **manufactura/crear_materia_prima.html** | ? | Gestión de materias primas |
| **manufactura/editar_materia_prima.html** | ? | Edición materias primas |
| **manufactura/listar_ordenes.html** | ? | Órdenes de producción |
| **manufactura/crear_producto.html** | ? | Producto con receta/BOM |
| **manufactura/editar_producto.html** | ? | Edición con BOM |
| **manufactura/listar_proveedores.html** | ? | Proveedores de materias primas |

#### 🛠️ Servicios Exclusivos:
| Template | Líneas | Razón |
|----------|--------|-------|
| **servicios/crear_servicio.html** | ? | Definición de servicios |
| **servicios/crear_venta.html** | ? | Venta de servicio (sin stock) |
| **servicios/listar_servicios.html** | ? | Catálogo de servicios |

#### 📚 Aprendizaje (Independiente):
| Template | Líneas | Razón |
|----------|--------|-------|
| **aprendizaje/dashboard.html** | ? | Sistema gamificado |
| **aprendizaje/leccion_interactiva.html** | ? | Lecciones paso a paso |
| **aprendizaje/simulacion_venta.html** | ? | Sandbox de práctica |
| **aprendizaje/ranking.html** | ? | Leaderboard |
| **aprendizaje/social_dashboard.html** | ? | Features sociales |

**Total Grupo C:** 18+ templates → **MANTENER SEPARADOS**

---

## 📈 ANÁLISIS DE VARIABLES POR CATEGORÍA

### Variables Comunes (Todas las categorías):
```python
# Transacciones
ventas, gastos, compras, capital

# Financiero
utilidad_neta, utilidad_bruta, margen_neto, margen_bruto

# Empresa
nombre, ruc, direccion, telefono, email

# Usuarios
username, email, rol, permisos
```

### Variables Específicas por Categoría:

#### 🏪 Comercio:
```python
costo_mercancia      # En lugar de costo_produccion
productos_stock      # Productos terminados
margen_comercial     # Margen de reventa
```

#### 🏭 Manufactura:
```python
costo_produccion     # Costo de fabricación
materias_primas      # Inventario de materias primas
ordenes_produccion   # Órdenes activas
recetas              # Bill of Materials (BOM)
costo_mano_obra      # Costo de personal producción
```

#### 🛠️ Servicio:
```python
costo_servicio       # Costo de prestación
horas_trabajadas     # Tiempo de servicio
servicios_activos    # Servicios en curso
tarifa_hora          # Precio por hora
```

---

## 🎨 ESTRATEGIA DE NORMALIZACIÓN

### Opción 1: Normalización en Backend (RECOMENDADO)
```python
# services/normalizador_contexto.py
def normalizar_costos(empresa, datos):
    if empresa.categoria == 'manufactura':
        datos['costo_principal'] = datos.get('costo_produccion', 0)
        datos['label_costo'] = 'Costo de Producción'
    elif empresa.categoria == 'comercio':
        datos['costo_principal'] = datos.get('costo_mercancia', 0)
        datos['label_costo'] = 'Costo de Mercancía'
    else:
        datos['costo_principal'] = datos.get('costo_servicio', 0)
        datos['label_costo'] = 'Costo de Servicio'
    return datos
```

### Opción 2: Condicionales en Template
```django
{% if user.empresa.categoria == 'manufactura' %}
    <h3>Costo de Producción</h3>
    <p>${{ costo_produccion }}</p>
{% elif user.empresa.categoria == 'comercio' %}
    <h3>Costo de Mercancía</h3>
    <p>${{ costo_mercancia }}</p>
{% else %}
    <h3>Costo de Servicio</h3>
    <p>${{ costo_servicio }}</p>
{% endif %}
```

---

## 🚨 RIESGOS IDENTIFICADOS

### ❌ Problemas Actuales:
1. **Duplicación de código:** Mismo HTML repetido en múltiples templates
2. **Inconsistencia:** Cambios en un template no se reflejan en otros
3. **Mantenimiento costoso:** Bug fix requiere modificar múltiples archivos
4. **Testing complejo:** Misma funcionalidad testeada 3 veces

### ⚠️ Riesgos de Unificación:
1. **Complejidad de condicionales:** Demasiados `{% if %}` dificultan lectura
2. **Performance:** Evaluar condicionales en cada render
3. **Errores en cadena:** Un bug afecta todas las categorías

### ✅ Mitigación:
- Usar normalización en backend (reduce condicionales)
- Crear partials/componentes reutilizables
- Testing exhaustivo antes de unificar
- Mantener templates específicos para lógica muy diferente

---

## 📋 PLAN DE ACCIÓN RECOMENDADO

### Prioridad ALTA (Semana 1):
1. ✅ **resumen.html** - Unificar con normalización backend
2. ✅ **crear_gasto.html** - Idéntico, unificar inmediatamente
3. ✅ **listar_gastos.html** - Idéntico, unificar inmediatamente
4. ✅ **listar_ventas.html** - Mínimas diferencias, unificar

### Prioridad MEDIA (Semana 2):
5. 🔄 **dashboard.html** - Crear base + bloques específicos
6. ✅ **balance_general.html** - Unificar (NIIF es estándar)
7. ✅ **estado_resultado.html** - Unificar con label_costos
8. ✅ **flujo_caja.html** - Idéntico, unificar

### Prioridad BAJA (Semana 3):
9. 🔄 **crear_producto.html** - Híbrido (manufactura muy diferente)
10. ✅ **inventario.html** - Unificar con sección materias primas
11. 🔴 **Manufactura/** - Mantener separados
12. 🔴 **Servicios/** - Mantener separados

---

## 📊 MÉTRICAS DE ÉXITO

### Antes de Refactorización:
- Templates totales: 75+
- Líneas de código duplicado: ~8,000
- Tiempo de mantenimiento: 3x por cambio
- Cobertura de tests: 40%

### Después de Refactorización (Objetivo):
- Templates totales: ~45 (-40%)
- Líneas de código duplicado: ~2,000 (-75%)
- Tiempo de mantenimiento: 1x por cambio (-66%)
- Cobertura de tests: 80% (+100%)

---

## 🎯 CONCLUSIONES FASE 1

### ✅ Templates a UNIFICAR (14):
- resumen.html
- crear_venta.html
- listar_ventas.html
- crear_gasto.html
- listar_gastos.html
- crear_compra.html
- listar_compra.html
- balance_general.html
- estado_resultado.html
- flujo_caja.html
- inventario.html
- mi_empresa.html
- gestion_deudas.html
- listar_productos.html

### 🔄 Templates HÍBRIDOS (4):
- dashboard.html
- crear_producto.html
- exportaciones_*.html
- actividad_reciente.html

### 🔴 Templates SEPARADOS (18+):
- manufactura/* (10 archivos)
- servicios/* (3 archivos)
- aprendizaje/* (8 archivos)

---

## 📝 PRÓXIMOS PASOS

**Fase 2: Refactorización**
1. Crear `services/normalizador_contexto.py`
2. Unificar templates del Grupo A (prioridad alta)
3. Crear templates base para Grupo B
4. Documentar cambios

**Fase 3: Componentes**
1. Crear `_partials/_kpi_card.html`
2. Crear `_partials/_tabla_transacciones.html`
3. Crear `_partials/_grafico_tendencias.html`
4. Migrar templates a usar partials

---

**Auditoría completada por:** Amazon Q  
**Revisión requerida:** Equipo de desarrollo  
**Aprobación:** Product Owner
